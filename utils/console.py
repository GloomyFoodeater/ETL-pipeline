import shutil

def print_centered(text: str, pad_char: str = "-") -> None:
    # Get current console width (fallback to 80 if unknown)
    width = shutil.get_terminal_size(fallback=(80, 20)).columns
    text = str(text)

    # If key is longer than the width, just print the key
    if len(text) >= width:
        print(text)
        return

    # Compute padding
    total_pad = width - len(text)
    left = total_pad // 2
    right = total_pad - left

    line = f"{pad_char * left}{text}{pad_char * right}"
    print(line)

