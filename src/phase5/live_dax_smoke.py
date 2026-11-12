"""Read-only live DAX acceptance via the locally installed Power BI MCP.

Run while Power BI Desktop has the refreshed WorkforceIntelligence model open.
Queries contain aggregate measures only; no employee identifiers are returned.
"""
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import threading
import time

from src.phase5.build_model import MEASURES

MCP_JS = Path(os.environ.get(
    "POWERBI_MCP_JS",
    r"D:\MCPServers\PowerBI\node_modules\@microsoft\powerbi-modeling-mcp\index.js",
))


class LocalMCP:
    def __enter__(self):
        node = shutil.which("node") or r"D:\node.exe"
        if not MCP_JS.exists() or not Path(node).exists():
            raise RuntimeError("Local Power BI MCP/Node is not installed")
        self.process = subprocess.Popen(
            [node, str(MCP_JS), "--start"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            encoding="utf-8", errors="replace", text=True,
        )
        self.replies = queue.Queue()

        def pump():
            for line in self.process.stdout:
                try:
                    self.replies.put(json.loads(line))
                except json.JSONDecodeError:
                    continue

        threading.Thread(target=pump, daemon=True).start()
        self.request("initialize", {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "workforce-phase5-dax-smoke", "version": "1.0"},
        })
        self.process.stdin.write(
            '{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
        self.process.stdin.flush()
        return self

    def __exit__(self, *_):
        self.process.terminate()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.kill()

    def request(self, method, params, timeout=40):
        request_id = getattr(self, "request_id", 0) + 1
        self.request_id = request_id
        self.process.stdin.write(json.dumps({
            "jsonrpc": "2.0", "id": request_id,
            "method": method, "params": params,
        }) + "\n")
        self.process.stdin.flush()
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try:
                item = self.replies.get(timeout=max(0.01, end - time.monotonic()))
            except queue.Empty:
                break
            if item.get("id") == request_id:
                if item.get("error"):
                    raise RuntimeError("Power BI MCP request failed")
                return item
        raise TimeoutError("Power BI MCP did not respond")

    def tool(self, name, request):
        response = self.request("tools/call", {
            "name": name, "arguments": {"request": request},
        })["result"]
        if response.get("isError"):
            msg = json.loads(response["content"][0]["text"]).get("message", "")
            # Do not copy SQL connector strings or any private model data into errors.
            raise RuntimeError(f"Power BI MCP {name} failed: {msg[:180]}")
        return json.loads(response["content"][0]["text"])

    def query(self, dax):
        result = self.tool("dax_query_operations", {
            "operation": "Execute", "query": dax,
            "resultMode": "Inline", "timeoutSeconds": 30,
        })
        rows = result.get("data", {}).get("rows", [])
        if len(rows) != 1:
            raise AssertionError("Expected exactly one aggregate row")
        return {key.strip("[]"): value for key, value in rows[0].items()}


def expect(actual, expected, label, tolerance=0.000001):
    if expected is None:
        ok = actual is None
    elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
        ok = actual is not None and abs(actual - expected) <= tolerance
    else:
        ok = actual == expected
    if not ok:
        raise AssertionError(f"{label}: unexpected DAX result")


def main():
    with LocalMCP() as mcp:
        instances = mcp.tool("connection_operations", {"operation": "ListLocalInstances"})
        available = instances.get("data", [])
        target = next((x for x in available
                       if x.get("parentWindowTitle") == "WorkforceIntelligence"), None)
        # After a PBIR preview, Desktop may temporarily expose an empty
        # window title. Only accept that case when there is exactly one
        # Desktop engine; verify its schema before issuing any DAX queries.
        if target is None and len(available) == 1:
            candidate = available[0]
            if candidate.get("parentProcessName") == "PBIDesktop":
                target = candidate
        if target is None:
            raise RuntimeError("Open and refresh WorkforceIntelligence in Power BI Desktop")
        mcp.tool("connection_operations", {
            "operation": "Connect", "connectionString": target["connectionString"],
        })
        live_tables = mcp.tool("table_operations", {"operation": "List"}).get("data", [])
        live_names = {t["name"] for t in live_tables}
        host = next((t for t in live_tables if t["name"] == "_Measures"), {})
        if not {"Dim Month", "Fact Workforce", "Fact Planning", "_Measures"} <= live_names:
            raise RuntimeError("Connected Power BI instance is not WorkforceIntelligence")
        if host.get("measureCount") != len(MEASURES):
            raise RuntimeError("Power BI measure count does not match the expected model")

        # Exercise every authored measure in a real DAX evaluation context.
        tested = 0
        for start in range(0, len(MEASURES), 10):
            chunk = MEASURES[start:start + 10]
            body = ",".join(f'"{m["name"]}",[{m["name"]}]' for m in chunk)
            row = mcp.query("EVALUATE ROW(" + body + ")")
            if set(row) != {m["name"] for m in chunk}:
                raise AssertionError("Missing or unexpected measure in DAX response")
            tested += len(chunk)

        december = mcp.query("""EVALUATE CALCULATETABLE(
          ROW("HC",[Ending Headcount],"Plan",[Planned Headcount],
              "Gap",[Headcount Gap],"FTE",[Ending FTE]),
          'Dim Month'[month]=DATE(2025,12,1))""")
        for key, expected in {"HC": 999, "Plan": 1079, "Gap": -80,
                              "FTE": 968.6}.items():
            expect(december[key], expected, key)

        jan = mcp.query("""EVALUATE CALCULATETABLE(
          ROW("HC",[Ending Headcount],"Attrition",[Monthly Attrition %]),
          'Dim Month'[month]=DATE(2023,1,1))""")
        expect(jan["HC"], 622, "Jan 2023 HC")
        expect(jan["Attrition"], None, "Jan 2023 attrition")

        annual = mcp.query("""EVALUATE CALCULATETABLE(
          ROW("HC",[Ending Headcount],"Rate",[Period Attrition %]),
          'Dim Month'[year]=2025)""")
        expect(annual["HC"], 999, "2025 stock")
        expect(annual["Rate"], 0.14725808513358046, "2025 period attrition")

        location = mcp.query("""EVALUATE CALCULATETABLE(
          ROW("Plan",[Planned Headcount],
              "Reconciliation",[Snapshot Reconciliation Difference]),
          TREATAS({"L001"},'Dim Location'[location_id]))""")
        expect(location["Plan"], None, "Unallocatable location plan")
        expect(location["Reconciliation"], None, "Company-only reconciliation")

        quality = mcp.query("""EVALUATE ROW(
          "People",[Observed Employees],"Exited",[Exited Employees],
          "ReviewMonths",[Reconciliation Review Months],
          "Pipeline",[Latest Pipeline Status],"Failures",[Latest Quality FAIL])""")
        for key, expected in {
            "People": 1200, "Exited": 206, "ReviewMonths": 33,
            "Pipeline": "SUCCEEDED", "Failures": 0,
        }.items():
            expect(quality[key], expected, key)
        print(json.dumps({
            "status": "PASS", "live_dax_measures_executed": tested,
            "scenario_checks": 15,
            "report": "WorkforceIntelligence",
        }))


if __name__ == "__main__":
    main()
