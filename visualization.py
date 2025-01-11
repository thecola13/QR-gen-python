from qrcode import QR
from PIL import Image, ImageDraw
from utils import console_log

def render_qr(qr, resolution = 300, border = 2):
    """
    Renders a QR code as an image.
    Args:
        qr (QR object): An object representing the QR code.
        resolution (int, optional): The resolution of the output image in pixels. Default is 300.
        border (int, optional): The width of the border around the QR code in cells. Default is 2.
    Returns:
        Image: A PIL Image object representing the rendered QR code.
    """

    scale = max(resolution // (qr.size + 4), 10)

    # Adjust the image size to include the border
    img_size = (qr.size + 2 * border) * scale # border set by default at 2 cells
    img = Image.new("1", (img_size, img_size), 1)  # Start with a completely white image
    
    # Draw the QR code on the canvas
    for y in range(qr.size):
        for x in range(qr.size):
            if qr.blocks[y][x]:
                for dy in range(scale):
                    for dx in range(scale):
                        img.putpixel(((x + border) * scale + dx, (y + border) * scale + dy), 0)
    return img

###############    Debug visualizations    ###############

def visualize_pointer_movement(qr, scale=10, border=4):
    """
    Visualizes the pointer movement during QR code generation as an image.
    Args:
        qr (QR object): An object representing the QR code.
        scale (int, optional): The scaling factor for the QR code cells. Default is 10.
        border (int, optional): The width of the border around the QR code in cells. Default is 4.
    Returns:
        Image: A PIL Image object representing the QR code with visualized pointer movement.
    """


    # Adjust image size
    img_size = (qr.size + 2 * border) * scale
    img = Image.new("RGBA", (img_size, img_size), (255, 255, 255, 255))  # White background

    # Overlay the QR code in the background with transparency
    overlay = Image.new("RGBA", (img_size, img_size), (255, 255, 255, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    for y in range(qr.size):
        for x in range(qr.size):
            if qr.blocks[y][x]:
                draw_overlay.rectangle(
                    [
                        ((x + border) * scale, (y + border) * scale),
                        ((x + border + 1) * scale - 1, (y + border + 1) * scale - 1),
                    ],
                    fill=(0, 0, 0, 128),  # Semi-transparent black
                )

    # Initialize drawing on the main image
    draw = ImageDraw.Draw(img)
    last_pos = None  # Track the last pointer position

    # Simulate `set_data_bytes` to visualize the pointer movement
    i = 0  # Index for the payload
    for x in range(qr.size - 1, 0, -2):  # Right column in each pair
        if x <= 6:
            x -= 1

        for y in range(qr.size):  # Vertical traversal
            for j in range(2):  # Two columns in the pair
                posx = x - j
                upward = (x + 1) & 2 == 0
                posy = (qr.size - 1 - y) if upward else y

                if not qr.isfunction[posy][posx]:
                    # Calculate real coordinates
                    real_x = (posx + border) * scale + scale // 2
                    real_y = (posy + border) * scale + scale // 2

                    # Draw a red dot for the pointer position
                    draw.ellipse(
                        [
                            (real_x - 2, real_y - 2),
                            (real_x + 2, real_y + 2),
                        ],
                        fill="red",
                    )

                    # Draw a line connecting the previous dot to the current dot
                    if last_pos:
                        draw.line([last_pos, (real_x, real_y)], fill="red", width=1)
                    last_pos = (real_x, real_y)

    # Composite the QR code overlay onto the main image
    img = Image.alpha_composite(img, overlay)
    return img

def render_function_blocks(qr, scale=10, border=4):
    """
    Renders the QR code with the function blocks highlighted as red dots.
    
    Args:
        qr (QR object): An object representing the QR code.
        scale (int, optional): The scaling factor for the QR code cells. Default is 10.
        border (int, optional): The width of the border around the QR code in cells. Default is 4.
    
    Returns:
        Image: A PIL Image object representing the QR code with function blocks highlighted.
    """

    # Adjust the image size
    img_size = (qr.size + 2 * border) * scale

    # Create a white image
    img = Image.new("RGB", (img_size, img_size), "white")
    draw = ImageDraw.Draw(img)

    # Draw the QR code in the background
    for y in range(qr.size):
        for x in range(qr.size):
            if qr.blocks[y][x]:
                for dy in range(scale):
                    for dx in range(scale):
                        img.putpixel(((x + border) * scale + dx, (y + border) * scale + dy), (0, 0, 0))

    # Overlay function blocks with red dots
    for y in range(qr.size):
        for x in range(qr.size):
            if qr.isfunction[y][x]:
                center_x = (x + border) * scale + scale // 2
                center_y = (y + border) * scale + scale // 2
                draw.ellipse(
                    [
                        (center_x - scale // 4, center_y - scale // 4),
                        (center_x + scale // 4, center_y + scale // 4),
                    ],
                    fill="red",
                )

    return img