SHELL=/bin/bash

.SECONDARY:

convert-% : teitok/ic16core_csen/%-en.xml teitok/ic16core_csen/%-cs.xml
	@echo "$* converted."
teitok/ic16core_csen/%-en.xml : data/ic16core_csen/%.en-00.tag.xml data/ic16core_csen/%.cs-00.en-00.alignment.xml
	cat $(word 1,$^) | python scripts/ic2teitok.py --salign-file $(word 2,$^) --align-ord 0 | sed 's/ xmlns="[^"]*"//g' > $@
teitok/ic16core_csen/%-cs.xml : data/ic16core_csen/%.cs-00.tag.xml data/ic16core_csen/%.cs-00.en-00.alignment.xml
	cat $(word 1,$^) | python scripts/ic2teitok.py --salign-file $(word 2,$^) --align-ord 1 | sed 's/ xmlns="[^"]*"//g' > $@


prewalign-% : walign/ic16core_csen/%.for_align.txt
	@echo "Files for word alignment of $* ready."
walign/ic16core_csen/%.for_align.txt : data/ic16core_csen/%.en-00.tag.xml data/ic16core_csen/%.cs-00.tag.xml data/ic16core_csen/%.cs-00.en-00.alignment.xml
	mkdir -p walign/ic16core_csen
	python scripts/add_w_ids.py \
		< $(word 1,$^) \
		> walign/ic16core_csen/$*.en-00.tag.with_wid.xml
	python scripts/add_w_ids.py \
		< $(word 2,$^) \
		> walign/ic16core_csen/$*.cs-00.tag.with_wid.xml
	python scripts/ic4aligner.py \
		$(word 3,$^) \
		walign/ic16core_csen/$*.en-00.tag.with_wid.xml \
		walign/ic16core_csen/$*.cs-00.tag.with_wid.xml \
		--output-ids walign/ic16core_csen/$*.for_align_ids.txt \
		> $@

walign-% : walign/ic16core_csen/%.align.txt
	@echo "Word alignment for $* ready."
walign/ic16core_csen/%.align.txt : walign/ic16core_csen/%.for_align.txt
	awesome-align \
		--output_file=walign/ic16core_csen/$*.align.pcedt-chp5000_sup-all-train.txt \
		--model_name_or_path=/home/mnovak/projects/word_align/models/awesomealign_models/pcedt-chp5000_sup-all-train \
		--data_file=$< \
		--extraction 'softmax' --batch_size 32 --num_workers 1
	ln -s $*.align.pcedt-chp5000_sup-all-train.txt $@

postwalign-% : walign/ic16core_csen/%-align_encs.xml
	@echo "Word alignment XML $* ready."
walign/ic16core_csen/%-align_encs.xml : walign/ic16core_csen/%.for_align_ids.txt walign/ic16core_csen/%.align.txt
	python scripts/compile_walign_xml.py \
			$(word 1,$^) \
			$(word 2,$^) \
		| xmllint --format - \
			> $@


############################################## SAMPLE ########################################################

sample :
	cat data/ic16core_csen/ackroyd-londyn.cs-00.tag.xml | sed '27289,323760d' > data/sample.cs.xml
	cat data/ic16core_csen/ackroyd-londyn.en-00.tag.xml | sed '31667,371796d' > data/sample.en.xml
	cat data/ic16core_csen/ackroyd-londyn.cs-00.en-00.alignment.xml | sed '1157,13508d' > data/sample.cs-en.align.xml

convert-sample :
	cat data/sample.en.xml | python scripts/ic2teitok.py --salign-file data/sample.cs-en.align.xml --align-ord 0 | sed 's/ xmlns="[^"]*"//g' > teitok/sample-en.xml
	cat data/sample.cs.xml | python scripts/ic2teitok.py --salign-file data/sample.cs-en.align.xml --align-ord 1 | sed 's/ xmlns="[^"]*"//g' > teitok/sample-cs.xml

convert-sample-noalign :
	cat data/sample.en.xml | python scripts/ic2teitok.py | sed 's/xmlns="[^"]*"//g' > teitok/sample-noalign-en.xml
	cat data/sample.cs.xml | python scripts/ic2teitok.py | sed 's/xmlns="[^"]*"//g' > teitok/sample-noalign-cs.xml

