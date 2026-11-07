{% macro generate_schema_name(custom_schema_name, node) -%}
  {# Separate staging/intermediate from marts without dbt target prefixes. #}
  {%- if custom_schema_name is none -%}
    {{ target.schema }}
  {%- else -%}
    {{ custom_schema_name | trim }}
  {%- endif -%}
{%- endmacro %}
