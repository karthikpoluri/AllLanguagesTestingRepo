import json
from paddleocr import PaddleOCR

# -----------------------------
# STEP 1: Run OCR
# -----------------------------
ocr = PaddleOCR(use_angle_cls=True, lang='en')

image_path = "image.png"

result = ocr.ocr(image_path, cls=True)[0]


# -----------------------------
# STEP 2: Extract structured blocks
# -----------------------------
blocks = []

# Get image width/height approx
all_x = []
all_y = []

for line in result:
    for p in line[0]:
        all_x.append(p[0])
        all_y.append(p[1])

width = max(all_x)
height = max(all_y)

for i, line in enumerate(result):
    box = line[0]
    text = line[1][0]
    conf = line[1][1]

    x_min = min(p[0] for p in box)
    y_min = min(p[1] for p in box)
    x_max = max(p[0] for p in box)
    y_max = max(p[1] for p in box)

    blocks.append({
        "id": i,
        "text": text,
        "confidence": float(conf),
        "bbox": [x_min, y_min, x_max, y_max],
        "norm_bbox": [
            x_min / width, y_min / height,
            x_max / width, y_max / height
        ],
        "center": [
            (x_min + x_max) / 2,
            (y_min + y_max) / 2
        ],
        "font_size": y_max - y_min
    })


# -----------------------------
# STEP 3: Sort + group into lines
# -----------------------------
blocks = sorted(blocks, key=lambda x: x["center"][1])

avg_height = sum(b["font_size"] for b in blocks) / len(blocks)
threshold = avg_height * 0.6

lines = []

for block in blocks:
    placed = False
    for line in lines:
        if abs(line[0]["center"][1] - block["center"][1]) < threshold:
            line.append(block)
            placed = True
            break
    if not placed:
        lines.append([block])

# Sort each line left → right
for line in lines:
    line.sort(key=lambda x: x["center"][0])


# -----------------------------
# STEP 4: Assign line_id + region + column
# -----------------------------
mid_x = width / 2

for line_id, line in enumerate(lines):
    for block in line:
        block["line_id"] = line_id

        y_min = block["bbox"][1]

        # region (top/middle/bottom)
        if y_min < height * 0.2:
            region = "top"
        elif y_min > height * 0.7:
            region = "bottom"
        else:
            region = "middle"

        block["region"] = region

        # column (left/right)
        if block["center"][0] < mid_x:
            block["column"] = "left"
        else:
            block["column"] = "right"


# -----------------------------
# STEP 5: Create readable layout
# -----------------------------
readable_lines = []

for line in lines:
    text_line = " ".join([b["text"] for b in line])
    readable_lines.append(text_line)

readable_text = "\n".join(readable_lines)


# -----------------------------
# STEP 6: Final JSON
# -----------------------------
final_output = {
    "image_size": {
        "width": width,
        "height": height
    },
    "blocks": blocks
}

print("\n====== READABLE TEXT ======\n")
print(readable_text)

print("\n====== JSON (for LLM) ======\n")
print(json.dumps(final_output, indent=2))

def save_json(final_output):
    with open("final_output.json", "w") as f:
        json.dump(final_output, f, indent=2)

save_json(final_output)


# -----------------------------
# STEP 7: LLM PROMPT (READY)
# -----------------------------
llm_prompt = f"""
You are given OCR output with spatial layout.

IMPORTANT RULES:
- Larger text = more important
- Top area = titles/company
- Nearby text belongs together
- Left/right columns may be different sections

TASK:
Extract:
- Name
- Company
- Phone numbers
- Email
- Address
- Website

----------------------
READABLE LAYOUT:
{readable_text}

----------------------
STRUCTURED JSON:
{json.dumps(final_output)}
"""

print("\n====== LLM PROMPT ======\n")
print(llm_prompt)

def save_llm_prompt_as_txt(llm_prompt):
    with open("final_prompt.txt", "w") as f:
        f.write(llm_prompt)

save_llm_prompt_as_txt(llm_prompt)



def generate_spatial_text(blocks, width, height, cols=80, rows=40):
    """
    Convert OCR blocks into a text grid
    """

    # Create empty grid
    grid = [[" " for _ in range(cols)] for _ in range(rows)]

    for b in blocks:
        text = b["text"]

        # Normalize position
        x_center = b["center"][0] / width
        y_center = b["center"][1] / height

        col = int(x_center * (cols - 1))
        row = int(y_center * (rows - 1))

        # Place text in grid
        for i, char in enumerate(text):
            if col + i < cols:
                grid[row][col + i] = char

    # Convert grid to string
    lines = ["".join(row).rstrip() for row in grid]
    return "\n".join(lines)


spatial_text = generate_spatial_text(blocks, width, height)
print("\n====== SPATIAL TEXT ======\n")
print(spatial_text)

def save_spatial_text_as_txt(spatial_text):
    with open("spatial_text.txt", "w") as f:
        f.write(spatial_text)

save_spatial_text_as_txt(spatial_text)
