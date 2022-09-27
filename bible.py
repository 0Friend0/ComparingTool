from calendar import c
import io
import re
import pandas as pd
import time
import jellyfish
from difflib import SequenceMatcher
from tqdm import tqdm

class BibleComparison():

    def __init__(self) -> None:
        
        self.file1_text = ""
        self.file2_text = ""
        self.list_1 = []
        self.list_2 = []
        self.new_sections = []
        self.edited_sections = []
        self.same_sections = []
        self.deleted_sections = []
        self.old_index_of_2_chapter = 0
        self.new_index_of_2_chapter = 0
        self.second_chapter_found = False

    def get_text(self, file):
    # Read file and return text
        file_readed = io.open(file, mode="r", encoding="utf-8")
        text = file_readed.read()

        text_short = text[text.find('Inhalt')+7:]
        return text, text_short

    def get_chapter_list(self, text_short):
    # Gets list of all chapters in text
        string = ""
        found_letter = False
        check = True
        multiple_lines = ""
        for line in text_short.splitlines():
            if line == "":
                continue
            line_litter = re.search('[a-zA-Z]', line)
            if not line_litter:
                multiple_lines = multiple_lines + line
                continue
            else:
                line = multiple_lines + line
                multiple_lines = ""
            try:

                if not check:
                    string, check = BibleComparison.char_in_line_processing(line, string)
                    continue
                if line[0].isdigit():
                    string = ""
                    string, check = BibleComparison.char_in_line_processing(line, string)
                    string = string.replace("  ", " ")

                    if len(self.list_1) == 0:
                        string = string.rstrip()
                        self.list_1.append(string)
                    elif string in self.list_1:
                        break
                    elif string[0] >= self.list_1[-1][0]:
                        string = string.rstrip()
                        self.list_1.append(string)
                    elif string[0] < self.list_1[-1][0]:
                        break

            except Exception as e:
                print(e)
                continue

    def char_in_line_processing(self, line, string):
    # Function that checks each letter in chapter name and filter "." and other characters
        found_letter = False
        for char in line:
            if found_letter and char != '.':
                string = string+char
                continue
            elif found_letter and char == '.':
                break
            if char.isalpha():
                string = string+char
                found_letter = True
            else: 
                if char.isnumeric() or char == "." or char == " ":
                    string = string+char
        try:
            letter = re.search('[a-zA-Z]', string)
            check = letter[0].isalpha()
        except:
            check = False
        return string, check

    def compare_lists(self):
    # Comparing 2 list with chapters and look for new and deleted ones
        for section in self.list_2:
            if section in self.list_1:
                pass
            else:
                letter = re.search('[a-zA-Z]', section)
                letter_index = letter.start()
                if section[letter.start()-2] == ".":
                    section_mod = section[:letter_index-2] + section[letter_index-1:]
                else:
                    section_mod = section[:letter_index-1] + "." + section[letter_index-1:]
                if section_mod in self.list_1:
                    pass
                else:
                    self.new_sections.append(section)
        
        for section in self.list_1:
            if section not in self.list_2:
                self.deleted_sections.append(section)


    def get_chapter_index(self, chapter_list, file_text):
        chapters = []
        # Find indexes where chapter was found
        for chapter in chapter_list:
            result = [m.start() for m in re.finditer(chapter, file_text)]

            if result == []:
                chapter = chapter[:10]
                result = [m.start() for m in re.finditer(chapter, file_text)]
                chapters.append(result)
            else:
                chapters.append(result)

        # Zip together chapter list with their indexes in text
        list_with_chapter_index = [list(a) for a in zip(chapter_list, chapters)]
        return list_with_chapter_index

    def get_chapter_text(self, section, section_index, list_with_chapters, file_text, index_of_2_chapter):
    # Gets text of chapter
        for start_index_of_text in section[1]:
                result = BibleComparison.test_section_index(start_index_of_text, file_text, list_with_chapters, index_of_2_chapter)

                if result:
                    try:
                        for start_index_of_next_chap in list_with_chapters[section_index+1][1]:
                            result_next_chap = BibleComparison.test_section_index(start_index_of_next_chap, file_text, list_with_chapters, index_of_2_chapter, start_index_of_text)
                            if result_next_chap:
                                return file_text[start_index_of_text:start_index_of_next_chap].replace('\n', ' ')
                    except IndexError:
                        for start_index_of_next_chap in list_with_chapters[section_index][1]:
                            result_next_chap = BibleComparison.test_section_index(start_index_of_next_chap, file_text, list_with_chapters, index_of_2_chapter, start_index_of_text)
                            if result_next_chap:
                                return file_text[start_index_of_text:start_index_of_next_chap].replace('\n', ' ')
                            

    def test_section_index(self, start_index_of_text, text, list_with_chapters, index_of_chapter_2, prev_chap_section=0):
    # Test index at which chapters starts. Checks if its a real chapter and not just a mention or a list.
        if start_index_of_text < list_with_chapters[0][1][1]:
            # When index of chapter is lower than 1st chapter (it means its a table of contents)
            return False
        matches = ['Kapitel', 'siehe', 'unter']
        if any(substring in text[start_index_of_text-12:start_index_of_text] for substring in matches):
            # When chapter is in headings or is mentioned in text
            return False
        if prev_chap_section > start_index_of_text:
            # When chapter index is lower that previous chapter (due to mistake or unexpected occurence)
            return False
        if start_index_of_text < index_of_chapter_2 and index_of_chapter_2 != 0 and self.second_chapter_found:
            # Making sure its not a mention in other chapter
            return False
            
        return True    

    def chapter_diff(self, list_with_chapter_index_1, list_with_chapter_index_2):
    # Find section that is not in self.new_sections from new file.
        # pbar = tqdm(desc="Processing", total=len(list_with_chapter_index_2))
        for section_index, section in tqdm(enumerate(list_with_chapter_index_2), total=len(list_with_chapter_index_2)):
            # print(section_indindex+1)
            # Sometimes chapters are mentioned in chapter 1.2. This checks if we are passed that chapter
            if section[0] == "2 Überblick":
                self.second_chapter_found
                self.second_chapter_found = True
                self.new_index_of_2_chapter = section[1][-1]

            if section[0] in self.new_sections:
                # Chapter already exists in new chapters
                continue
    # Get text of the chapter from new file.
            try:
                index_of_2_chapter = self.new_index_of_2_chapter
            except UnboundLocalError:
                index_of_2_chapter = 0
            chapter_text_new = BibleComparison.get_chapter_text(section, section_index, list_with_chapter_index_2, self.file2_text, index_of_2_chapter)
    # Get text of chapter from old file.
            for section_index_old, section_old in enumerate(list_with_chapter_index_1):
                if section_old[0] == "2 Überblick":
                    self.old_index_of_2_chapter = section_old[1][-1]
                # print(section_index_old, section_old)
                if section_old[0] == section[0]:
                    # Found same chapter names in old and new file
                    try:
                        index_of_2_chapter = self.old_index_of_2_chapter
                    except UnboundLocalError:
                        index_of_2_chapter = 0
                    chapter_text_old = BibleComparison.get_chapter_text(section_old, section_index_old, list_with_chapter_index_1, self.file1_text, index_of_2_chapter)

                    if chapter_text_new == chapter_text_old:
                        self.same_sections.append(section[0])
                        # Chapters have the same text (in new file chapter has not changed)
                    else:
                        # Calculate difference ratio and convert it to %
                        diff_ratio = SequenceMatcher(a=chapter_text_old, b=chapter_text_new).ratio()
                        diff_ratio = "{0:.1%}".format(diff_ratio)
                        # Calculate character changed 
                        changes_required = jellyfish.damerau_levenshtein_distance(chapter_text_old, chapter_text_new)
                        len_of_string_old = len(chapter_text_old)
                        len_of_string_new = len(chapter_text_new)
                        list_to_append = [section[0], diff_ratio, changes_required, len_of_string_old, len_of_string_new]
                        self.edited_sections.append(list_to_append)
                    continue
            

    def save_to_excel(self):
    # Saves all the data to excel file
        dt_new_sections = pd.DataFrame(self.new_sections, columns=["Chapter name"])
        dt_edited_sections = pd.DataFrame(self.edited_sections, columns=["Chapter name", "Difference ratio", "Characters changed", "Old file chapter characters", "New file chapter characters"])
        dt_list2 = pd.DataFrame(self.list_2, columns=["Chapter name"])
        dt_deleted_sections = pd.DataFrame(self.deleted_sections, columns=["Chapter name"])
        dt_same_sections = pd.DataFrame(self.same_sections, columns=["Chapter name"])

        writer = pd.ExcelWriter('Bible_results.xlsx', engine='xlsxwriter')
        dt_new_sections.to_excel(writer, sheet_name='new_chapters', index=False)
        dt_edited_sections.to_excel(writer, sheet_name='edited_chapters', index=False)
        dt_deleted_sections.to_excel(writer, sheet_name='deleted_chapters', index=False)
        dt_same_sections.to_excel(writer, sheet_name='unchanged_chapters', index=False)
        dt_list2.to_excel(writer, sheet_name='all_chapters', index=False)
        writer.save()

