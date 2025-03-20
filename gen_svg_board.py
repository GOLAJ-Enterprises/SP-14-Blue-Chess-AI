def generate_chessboard_svg(
    square_size=125,
    light_color="#f0d9b5",
    dark_color="#b58863",
    fill_opacity=0.1,  # New: control square transparency
):
    svg_width = square_size * 8
    svg_height = square_size * 8

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}">'
    ]

    for row in range(8):
        for col in range(8):
            color = light_color if (row + col) % 2 == 0 else dark_color
            x = col * square_size
            y = row * square_size
            svg_parts.append(
                f'<rect x="{x}" y="{y}" width="{square_size}" height="{square_size}" fill="{color}" fill-opacity="{fill_opacity}" />'
            )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


svg_content = generate_chessboard_svg()
with open("chessboard.svg", "w") as f:
    f.write(svg_content)
