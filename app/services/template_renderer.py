import re
from typing import Any

from app.models.template import Template


def render_template_content(
    template: Template,
    context: dict[str, Any],
) -> tuple[str, dict[str, Any], list[str]]:
    """
    Renders template.content by replacing {{var}} placeholders using the given context.

    Returns (rendered_text, used_variables, missing_variables).
    """
    content = template.content
    used_variables: dict[str, Any] = {}
    missing_variables: list[str] = []
    
    # Pattern to match {{variable_name}} placeholders
    # Matches {{ followed by variable name (alphanumeric + underscore) followed by }}
    pattern = r'\{\{(\w+)\}\}'
    
    def replace_placeholder(match: re.Match[str]) -> str:
        """Replace a single placeholder with its value or keep it if missing."""
        var_name = match.group(1)
        
        if var_name in context:
            value = context[var_name]
            used_variables[var_name] = value
            return str(value)
        else:
            missing_variables.append(var_name)
            return match.group(0)  # Keep the placeholder as is
    
    # Replace all placeholders
    rendered_text = re.sub(pattern, replace_placeholder, content)
    
    # Remove duplicates from missing_variables while preserving order
    missing_variables = list(dict.fromkeys(missing_variables))
    
    return rendered_text, used_variables, missing_variables

