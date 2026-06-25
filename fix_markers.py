files = [
    r"c:\Users\soumy\stock_dashB\ML_EXPLAINED.md",
    r"c:\Users\soumy\stock_dashB\backend\ml\random_forest_model.py",
    r"c:\Users\soumy\stock_dashB\backend\ml\linear_model.py",
    r"c:\Users\soumy\stock_dashB\backend\ml\base_model.py",
]

for file_path in files:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    new_lines = []
    state = "NORMAL"
    for line in lines:
        if line.startswith("<<<<<<< HEAD"):
            state = "HEAD"
        elif line.startswith("======="):
            state = "THEIRS"
        elif line.startswith(">>>>>>>"):
            state = "NORMAL"
        else:
            if state == "NORMAL" or state == "HEAD":
                new_lines.append(line)

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

print("Done fixing markers.")
