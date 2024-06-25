text_reset = "\x1b[0m"
bold_text = "\033[1m"


def escapeCode(text_color_rgb=None, bg_color_rgb=None, bold=False):
    """
    Convert RGB color values to ANSI escape code for 256-color mode.

    Parameters:
    - text_color_rgb (tuple or list): RGB values (0-255) for text color.
    - bg_color_rgb (tuple or list, optional): RGB values (0-255) for background color.
    - bold (bool, optional): Whether text should be bold (default: False).

    Returns:
    - str: ANSI escape code for the specified colors and style in 256-color mode.
    """
    if text_color_rgb is not None:
        if len(text_color_rgb) != 3:
            raise ValueError("Text color RGB tuple must contain exactly three values (R, G, B)")
        if not all(0 <= c <= 255 for c in text_color_rgb):
            raise ValueError("Text color RGB values must be between 0 and 255")

    escape_code = "\x1b["

    if bold and text_color_rgb is None and bg_color_rgb is None:
        return bold_text

    # Bold attribute
    if bold:
        escape_code += "1;"

    if text_color_rgb is not None:
        # Text color
        text_color_index = 16 + (36 * round(text_color_rgb[0] / 255 * 5)) + (
                6 * round(text_color_rgb[1] / 255 * 5)) + round(text_color_rgb[2] / 255 * 5)
        escape_code += f"38;5;{text_color_index}"

    # Background color
    if bg_color_rgb is not None:
        if len(bg_color_rgb) != 3:
            raise ValueError("Background color RGB tuple must contain exactly three values (R, G, B)")
        if not all(0 <= c <= 255 for c in bg_color_rgb):
            raise ValueError("Background color RGB values must be between 0 and 255")

        bg_color_index = 16 + (36 * round(bg_color_rgb[0] / 255 * 5)) + (6 * round(bg_color_rgb[1] / 255 * 5)) + round(
            bg_color_rgb[2] / 255 * 5)
        escape_code += f";48;5;{bg_color_index}"

    escape_code += "m"
    return escape_code


def formatString(string, color=None, background=None, bold=False):
    return_string = f"{escapeCode(text_color_rgb=color, bg_color_rgb=background, bold=bold)}{string}{text_reset}"
    return return_string
