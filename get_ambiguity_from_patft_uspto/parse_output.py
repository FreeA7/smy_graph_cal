

with open('output.txt', 'a', encoding='utf-8') as w:
    with open('output_20220910.txt', 'r', encoding='utf-8') as f:
        w.write(f.read())