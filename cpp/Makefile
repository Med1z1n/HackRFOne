CXX=g++
OBJS=main.o
EXE=hackrf
HEADERS=audio_file.h
CPPFLAGS=-Wall -Wextra -pedantic -g -std=c++23 -O2
LDFLAGS+=-lhackrf -lliquid --verbose

# default target
$(EXE): $(OBJS)
	$(CXX) $(CPPFLAGS) -o $(EXE) $(OBJS) $(LDFLAGS)

# source files
%.o: %.cc $(HEADERS)
	$(CXX) $(CPPFLAGS) -c $<

# phony target - remove generated files and backups
clean:
	rm -rf $(EXE) *.o *~ *.dSYM
