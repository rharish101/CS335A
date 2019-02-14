all: parser

parser:
	mkdir -p bin
	cp -t bin/ src/lexer.py src/parser.py src/go_classes.py
	ln -sf bin/parser.py myASTGenerator
	chmod +x myASTGenerator

clean:
	rm -rf bin myASTGenerator parser.out parsetab.py
