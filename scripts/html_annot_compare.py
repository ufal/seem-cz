import argparse
import logging
import os
import xml.etree.ElementTree as xmlparser

from jinja2 import Environment, FileSystemLoader, select_autoescape

from bookdoc import BookDoc
from markerdoc import MarkerDoc

# setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

# Initialize Jinja2 environment
template_env = Environment(
    loader=FileSystemLoader('.'),
    autoescape=select_autoescape(['html', 'xml'])
)
        
ANNOT_ATTRS = [
    ("dictexample", "Příklad do slovníku"),
    ("use", "Užití"),
    ("certainty", "Míra jistoty"),
    ("certaintynote", "Poznámka (míra jistoty)"),
    ("commfuntype", "Typ komunikační funkce"),
    ("commfunsubtype", "Konkrétní komunikační funkce"),
    ("commfunnote", "Poznámka (komunikační funkce)"),
    ("scope", "Dosah"),
    ("pred", "Predikát"),
    ("predlemma", "Predikát (lemma)"),
    ("predtag", "Predikát (tag)"),
    ("predverbtag", "Predikát (verbtag)"),
    ("member", "Člen"),
    ("tfpos", "Pozice v AČ"),
    ("sentpos", "Místo ve větě"),
    ("neg", "Přítomnost negace"),
    ("modalpersp", "Perspektiva modality"),
    ("modif", "Modifikace"),
    ("evidence", "Evidence"),
    ("evidencetype", "Typ evidence"),
    ("comment", "Komentář"),
]

BASE_ATTRS = [
    ("id", "ID"),
    ("cql", "CQL dotaz"),
    ("xml", "ID dokumentu"),
    ("cs", "Výraz v češtině (ID)"),
    ("cst", "Výraz v češtině (formy)"),
    ("en", "Výraz v angličtině (ID)"),
]

INDEX_ATTRS = {
    "cs": ["cs", "pred", "member", "modif", "evidence"],
    "en": ["en"],
}

# Initialize template data
def init_template_data(annot_names):
    data = {
        'title': "Comparison of SEEM-CZ parallel annotations",
        'annot_names': annot_names,
        'annot_attrs': ANNOT_ATTRS,
        'base_attrs': BASE_ATTRS,
    }
    return data

def deref_index_attrs_by_book(annotdoc, book, attrs):
    for annot_elem in annotdoc.annots_by_bookid(book.id):
        for attr_name in attrs:
            tok_deref_str = annot_elem.attrib.get(attr_name, "")
            tok_idxs = tok_deref_str.strip().split(" ")
            if tok_idxs and tok_idxs[0] in book.tok_index:
                tok_deref_str = " ".join([book.tok_index.get(tok_idx, tok_idx) for tok_idx in tok_idxs])
            elif tok_deref_str:
                tok_deref_str = f'"{tok_deref_str}"'
            annot_elem.attrib[attr_name + ".deref"] = tok_deref_str

def deref_index_attrs_all(doclist, bookdir):
    all_bookids = set(bookid for doc in doclist for bookid in doc.booklist)
    for bookid in all_bookids:
        for lang, attrs in INDEX_ATTRS.items():
            book = BookDoc(bookid, lang, bookdir)
            for i, doc in enumerate(doclist):
                logging.debug(f"Dereferencing index attributes to the {lang} version of {bookid} for the document no. {i+1}")
                deref_index_attrs_by_book(doc, book, attrs)

def extract_base_attrs(elem):
    return {attr_name: elem.attrib.get(attr_name, "") for attr_name, _ in BASE_ATTRS}

def extract_annot_attrs(elem_bundle):
    return {
        attr_name: {
            "annots": (values := [elem.attrib.get(deref_attr_name if (deref_attr_name := attr_name + ".deref") in elem.attrib else attr_name, "") for elem in elem_bundle]),
            "all_same": all([v == values[0] for v in values]),
            "all_empty": all([v == "" for v in values]),
        }
        for attr_name, _ in ANNOT_ATTRS
    }

def extract_attrs(elem_bundle):
    if len(elem_ids := list(set([elem.attrib["id"] for elem in elem_bundle]))) > 1:
        logging.error(f"Parallel annotations do not refer to the same example: {' '.join(elem_ids)}")
        exit()
    return {
        "base_attrs": extract_base_attrs(elem_bundle[0]),
        "annot_attrs": extract_annot_attrs(elem_bundle),
    }

def render_template(template_name, **context):
    # Load the template
    template = template_env.get_template(template_name)
    # Render the template with the provided context
    return template.render(**context)

def parse_arguments():
    parser = argparse.ArgumentParser(description="compare input annotation of markers and output the comparison in HTML")
    parser.add_argument("input_files", nargs="+", help="input files to be compared")
    parser.add_argument("--book-dir", type=str, help="directory with books in the teitok format")
    args = parser.parse_args()
    return args

def main():
    args = parse_arguments()
    
    if len(args.input_files) < 2:
        logging.error("More than one input files must be specified.")
        exit()

    doc_list = [MarkerDoc(filepath) for filepath in args.input_files]

    deref_index_attrs_all(doc_list, args.book_dir)
    
    all_results = [extract_attrs(annot_bundle) for annot_bundle in zip(*doc_list)]

    #logging.debug(f"{all_results = }")

    # Define the data to pass to the template
    data = init_template_data(annot_names=[os.path.basename(file) for file in args.input_files])
    data["results"] = all_results
    #logging.debug(f"{data = }")
    
    # Render the template
    rendered_html = render_template('template/compare_annot.html', **data)
    # Print or do whatever you want with the rendered HTML
    print(rendered_html)

if __name__ == "__main__":
    main()
