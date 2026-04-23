from docling.document_converter import DocumentConverter

#Implement method to pasrese through text file for the .pdf. 
#Make a variable with the assigned .pdf to put into the source varianle
#Convert pdf to JSON and send to a db

converter = DocumentConverter()
source = "https://docs.ccsu.edu/CampusMap.pdf"
doc = converter.convert(source).document
print(doc.export_to_markdown())

#https://www.docling.ai/#start 