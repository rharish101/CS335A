all: parser

parser:
	mkdir -p bin
	cp -t bin/ lexer.py parser.py go_classes.py
	ln -sf bin/parser.py myASTGenerator
	chmod +x myASTGenerator

clean:
	rm -rf bin myASTGenerator parser.out parsetab.py
