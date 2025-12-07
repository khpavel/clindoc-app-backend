import re
from typing import Any

from app.models.template import Template


def render_template_string(
    template_text: str,
    context: dict[str, Any],
) -> tuple[str, dict[str, Any], list[str]]:
    """
    Replace {{variable}} placeholders in template_text using values from context.

    Returns (rendered_text, used_variables, missing_variables).
    """
    used_variables: dict[str, str] = {}
    missing_variables: list[str] = []
    
    # Pattern to match {{variable_name}} where variable_name is [a-zA-Z0-9_]+
    pattern = r'\{\{([a-zA-Z0-9_]+)\}\}'
    
    def replace_placeholder(match: re.Match[str]) -> str:
        """Replace a single placeholder with its value or keep it if missing."""
        var_name = match.group(1)
        
        if var_name in context:
            value = context[var_name]
            # Convert value to string for used_variables (None becomes empty string)
            used_variables[var_name] = "" if value is None else str(value)
            return str(value) if value is not None else ""
        else:
            # Only add to missing_variables if not already present
            if var_name not in missing_variables:
                missing_variables.append(var_name)
            return match.group(0)  # Keep the placeholder unchanged
    
    # Replace all placeholders
    rendered_text = re.sub(pattern, replace_placeholder, template_text)
    
    return rendered_text, used_variables, missing_variables


def render_template_content(
    template: Template,
    context: dict[str, Any],
    language: str = "ru",
) -> tuple[str, dict[str, Any], list[str]]:
    """
    Convenience wrapper around render_template_string for Template instances.
    
    Args:
        template: Template instance to render
        context: Dictionary of variables for template substitution
        language: Language code ("ru" or "en") - accepted for future language-specific template logic
    
    Returns:
        Tuple of (rendered_text, used_variables, missing_variables)
    """
    # Note: language parameter is accepted but not yet used in template rendering
    # This prepares for future language-specific template processing
    return render_template_string(template.content, context)

