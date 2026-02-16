import re

input_file = "Fries.md"
output_file = "README.md"

with open(input_file, "r", encoding="utf-8") as f:
    content = f.read()

# заміна ![[image.png]] -> ![](images/image.png)
content = re.sub(r'!\[\[(.*?)\]\]', r'![](images/\1)', content)

# заміна [[note]] -> [note](note.md)
content = re.sub(r'\[\[(.*?)\]\]', r'[\1](\1.md)', content)

with open(output_file, "w", encoding="utf-8") as f:
    f.write(content)

print("Done!")
