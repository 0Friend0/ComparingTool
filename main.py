import time
from bible import BibleComparison

try:
    start_time = time.time()

    file1_text, file1_short = BibleComparison.get_text("old.txt")
    file2_text, file2_short_text = BibleComparison.get_text("new.txt")

    BibleComparison.get_chapter_list(file1_short)
    BibleComparison.get_chapter_list(file2_short_text)

    BibleComparison.compare_lists()

    list_with_chapter_index_1 = BibleComparison.get_chapter_index(file1_text)
    list_with_chapter_index_2 = BibleComparison.get_chapter_index(file2_text)

    BibleComparison.chapter_diff(list_with_chapter_index_1, list_with_chapter_index_2)
    BibleComparison.save_to_excel()
    print(f'Execution time: {time.time() - start_time}')
except Exception as e:
    print(e)

