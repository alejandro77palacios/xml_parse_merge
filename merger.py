from pathlib import Path

import pandas as pd

from parser import QuestionParser


class ChapterMerger:

    def __init__(self, chapter_directory):
        self.directory = chapter_directory
        self.xml_files = list(self.directory.glob('*.xml'))
        try:
            self.xml_files.remove(self.directory / 'imsmanifest.xml')
        except ValueError:
            print('Could not find imsmanifest.xml')
        self.xml_files = [file for file in self.xml_files if 'Essay' not in file.name]
        self.xml_files = sorted(self.xml_files, key=lambda x: int(x.name.split('_')[0].replace('Q', '').zfill(2)))

    def merge(self):
        print(f'Processing chapter {self.directory.name} with {len(self.xml_files)} files')
        tables = (QuestionParser(file).produce_table() for file in self.xml_files)
        return pd.concat(tables, ignore_index=True)


def export_chapters_in_independent_files():
    test_bank = Path('Test Bank - Canvas')
    target_directory = Path('output')
    target_directory.mkdir(exist_ok=True)
    for chapter in test_bank.iterdir():
        if chapter.is_dir():
            merger = ChapterMerger(chapter)
            df = merger.merge()
            print()
            file = target_directory / f'{chapter.name}.xlsx'
            if file.exists():
                print(f'File {file.name} already exists')
            else:
                df.to_excel(file, index=False)
                print(f'Saved {file.name}')


def export_in_one_file():
    test_bank = Path('Test Bank - Canvas')
    target_directory = Path('output')
    target_directory.mkdir(exist_ok=True)
    chapter_dirs = [chapter for chapter in test_bank.iterdir() if chapter.is_dir()]
    chapter_dirs = sorted(chapter_dirs, key=lambda x: int(x.name.split('_')[1].zfill(2)))
    dfs = (ChapterMerger(chapter_dir).merge() for chapter_dir in chapter_dirs)
    writer = pd.ExcelWriter('output.xlsx', engine='xlsxwriter')
    chapter_names = (chapter.name for chapter in chapter_dirs)
    for df, sheet_name in zip(dfs, chapter_names):
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    writer._save()
    print('Saved output.xlsx')


if __name__ == '__main__':
    # export_chapters_in_independent_files()
    export_in_one_file()
