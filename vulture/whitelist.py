# Whitelist for the vulture linter

from src.lintquarto.args import CustomArgumentParser
from docs.pages.helpers import print_quarto, generate_html

# The error method is called internally by argparse when the user provides
# invalid arguments, and does not need to be called directly from our code 
CustomArgumentParser.error

# Used in .qmd files
print_quarto
generate_html