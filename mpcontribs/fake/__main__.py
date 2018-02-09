import argparse
from .v1 import MPFakeFile

parser = argparse.ArgumentParser()
parser.add_argument("--main-general", action="store_true", help="""
                    contribution mode indicating whether the submitted file is
                    using a main general section or not. If so, all level-0
                    sections of the file belong to the same MP category ID. 
                    """)
parser.add_argument("--num-level0-sections", type=int, default=3, help="""
                    number of level-0 sections contained in the output.
                    """)
parser.add_argument("--max-level", type=int, default=3, help="""
                    maximum level/depth of subsection nesting.
                    """)
parser.add_argument("--max-num-subsec", type=int, default=3, help="""
                    maximum number of subsections of any level-n section.
                    """)
parser.add_argument("--max-data-rows", type=int, default=3, help="""
                    maximum number of data rows (csv or key:value).
                    """)
parser.add_argument("--mp-title-prob", type=int, default=50, help="""
                    probability (in int-percent) of MP level-1 titles.
                    """)
parser.add_argument("--usable", action="store_true", help="""
                    use baseball DB to generate usable MP input file
                    """)
args = vars(parser.parse_args())
f = MPFakeFile(**args)
mkf = f.make_file()
if mkf is not None:
    print(mkf.getvalue())
