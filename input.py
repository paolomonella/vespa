#!/usr/bin/env python
# -*- coding: utf-8 -*-

def publish_by_products(src,dest):
	"""
		This simply copies the files constituting the by-products of my digital edition
		to the local folder of my website on http://www.unipa.it/paolo.monella/lincei
	"""
	import os
	import shutil
	src_files = os.listdir(src)
	for file_name in src_files:
	    full_file_name = os.path.join(src, file_name)
	    if (os.path.isfile(full_file_name)):
	        shutil.copy(full_file_name, dest)

def de_parenthesize(string, start_parenthesis, close_parenthesis, previous_level_id):
    
    token_id = 0
    token_ref = ''
    parenthesis_mode = False
    table = {}
    
    for char in string:
        token_id = token_id + 1             # Sequential token id
        # Create sequences like "1.1", "1.2", "1.3" etc.
        str_token_id = previous_level_id+'.'+str(token_id)
        if char == start_parenthesis:
            parenthesis_mode = True
            # The counter should not keep running, so I'm bringing it back
            token_id = token_id - 1
        elif char == close_parenthesis:
            table[str_token_id]=token_ref
            token_ref = ''
            parenthesis_mode = False
        elif not parenthesis_mode:
            # This will become the XML/TEI @ref,
            # while the id will become the XML/TEI @id
            table[str_token_id]=char
        elif parenthesis_mode:
            token_ref += char
            # The counter should not keep running, so I'm bringing it back
            token_id = token_id - 1
    # The function returns a dictionary, where keys are the XML/TEI @id
    # and values are the XML/TEI @ref
    return table


def read_table_of_signs(table_file):
    # This function might be useless: I could just insert the code in teify1() or menotify()
    # sgn2
    """ Inputs a CSV file with a table of signs and outputs a dictionary where:
            - Keys: sign IDs;
            - values: lists (a_list) including all 'contents'
        I'm ignoring split_sign_expression and split_sign_digit_visualisation right now
        
    """

    with open(table_file,'r') as tbf:
        table = {}
        for tb_row in tbf.readlines():
                split_sign_id, split_sign_content, split_sign_expression, split_sign_digit_visualisation = tb_row.split('\t')
                expr_list = split_sign_content.split(',')  # This is a list
                table[split_sign_id] = expr_list
    return table


def charDecl(table_file):
    """ Opens a table of signs (graphemes or alphabemes) and creates
        the TEI charDecl element. It returns a string (including many
        rows), ready to be printed to a XML file
        
    """
    
    with open(table_file,'r') as tbf:
        s =     '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
        s = s + '<teiHeader>\n'
        s = s + '  <!-- ... -->\n'
        
        s = s + '  <charDecl>\n\n'
        for tb_row in tbf.readlines():
                split_sign_id, split_sign_content, split_sign_expression, split_sign_digit_visualisation = tb_row.split('\t')
                # expr_list = split_sign_content.split(',')  # This is a list # Not necessary
                s = s + '    <char xml:id= "'+split_sign_id+'">\n'
                s = s + '      <charProp>\n'
                s = s + '        <localName>Expression</localName>\n'
                s = s + '        <value>'+split_sign_expression+'</value>\n'
                s = s + '      </charProp>\n'
                s = s + '      <charProp>\n'
                s = s + '        <localName>Content</localName>\n'
                s = s + '        <value>'+split_sign_content+'</value>\n'
                s = s + '      </charProp>\n'
                s = s + '      <charProp>\n'
                s = s + '        <localName>Visualisation</localName>\n'
                s = s + '        <value>'+split_sign_digit_visualisation[:-1]+'</value>\n'
                s = s + '      </charProp>\n'
                s = s + '    </char>\n\n'
        s = s + '  </charDecl>\n'
        s = s + '</teiHeader>\n\n'
        s = s + '<text>\n'
        s = s + '<body>\n'
    return s
    

def teify1(transcription_file,graphemes_table,alphabemes_table):
        """ Transforms original transcription file into TEI.
            The transcription file is a CSV in which:
            1) the column to the left has sequences of graphemes, arranged in lines
            (a line per word). This arrangement is meant to allow this script to
            insert interpretative SEGs marking what I think are words at the linguistic
            level(something that is not present in the MS),
            so I can later more easily align graphic transcription
            with linguistic transcription;
            2) the column to the right has inflected words at linguistic layer.
            3) the divider is a "§" key.
            4) in the left colum,
               c(u_)
            means that the SEG has two graphemes:
              a. the first has grapheme-reference "c";
              b. the second has grapheme-reference "u_"
    
        """


        # OPEN FILES TO WRITE TO
        g_xml = open('salm_graphic.xml','w')
        a_xml = open('salm_alphabetic.xml','w')
        l_xml = open('salm_linguistic.xml','w')
        al_xml = open('salm_align_alph_ling.xml','w')
        gl_xml = open('salm_align_graph_ling.xml','w')
        ag_xml = open('salm_align_alph_graph.xml','w')

        # INPUT THE TABLES OF SIGNS
        # At the moment, I don't need to input the table of signs/alphabemes as a dictionary.
        # g_table is a dictionary where:
            #   Keys: grapheme-IDs;
            #   values: lists (a_list) including all alphabetical-REFs
            # I'm ignoring split_g_expression right now
        g_table = read_table_of_signs(graphemes_table)

        # INPUT TRANSCRIPTION
        trf = open(transcription_file,'r')
        tr_rows = trf.readlines()

        # WRITE TABLE OF SIGNS/GRAPHEMES TO TEI HEADER
        print(charDecl(graphemes_table),file=g_xml) #sgn4
        print(charDecl(alphabemes_table),file=a_xml) #sgn4

        # CYCLE WORDS IN TRANSCRIPTION
        # w_id: Sequential ID for any word in the transcription. It goes into
        #   <w id="1"> in the linguistic file
        w_id = 0
        for word in tr_rows:

            # INCREASE WORD COUNTER
            # As any line in the input file is a word in the MS, it creates a counter
            # for the TEI @id argument of the <w> element
            w_id = w_id + 1
            sw_id = str(w_id)   # This is simply a string corresponding to w_id (which is
                                # and integer). It is used to insert the ID in TEI/XML strings


            # SPLIT GRAPHEMATIC/LINGISTIC LAYERS
            tr_g_layer, tr_l_layer = word.split('§')    # tr_g_layer = graphical layer transcription,
                                                    # tr_l_layer = linguistic layer transcription
            tr_g_layer = tr_g_layer.rstrip().lstrip()
            tr_l_layer = tr_l_layer.rstrip().lstrip()

            # NON-WORDS (LINE BREAK, WORD BREAK, PUNCTUATION)
            # At graphemic layer, check for 'special lines', like "-." (punctuation),
            # "-wb" ("word break", space) or "-lb" (line break). It's not necessary to
            # align with linguistic layer (as they are not words) nor with alphabetic
            # layer (as they do not have alphabetic content)
            if tr_g_layer == '-lb':  # Line break
                # This does not have any correspondence at the linguistic layer (so far)
                print('<lb id="'+sw_id+'" />\n', file=g_xml)
            elif tr_g_layer == '-wb':  # Word brak (proposal of TEI modification)
                # This does not have any correspondence at the linguistic layer (so far)
                print('<wb id="'+sw_id+'" />\n', file=g_xml)
            elif tr_g_layer == '-indent':  # Indent at beginning of line
                # This does not have any correspondence at the linguistic layer (so far)
                print('<indent id="'+sw_id+'" />\n', file=g_xml)
            elif tr_g_layer[0] == '-':  # Stand-alone (not in a word) TEI <g> element
                # This does not have any correspondence at the linguistic layer (so far)
                # sgn: Is there a TEI element for paragraphematic signs? Is it OK that a
                #   grapheme occurs outside a word?
                print('<g id="'+sw_id+'" ref="#'+tr_g_layer.lstrip('-')+'" />\n', file=g_xml)
                g_ref = ''

            # REGULAR WORDS
            # If none of the previous 'special line'-cases applies, start a new word
            else:
                # In linguistic file
                # print('<w id="'+sw_id+'">'+tr_l_layer+'</w>', file=l_xml)
                print('<w id="'+sw_id+'" ana="'+tr_l_layer+'" /w>', file=l_xml)

                # Align word (at ling. layer) with a sequence of graphemes
                print('<link targets="salm_linguistic.xml#'+sw_id+' #'+sw_id+'" />', file=gl_xml)
                print('<ptr id="'+sw_id+'" targets=\n\t\t"', sep='', end='', file=gl_xml)

                # Align word (at ling. layer) with a sequence of alphabetical units
                print('<link targets="salm_linguistic.xml#'+sw_id+' #'+sw_id+'" />', file=al_xml)
                print('<ptr id="'+sw_id+'" targets=\n\t\t"', sep='', end='', file=al_xml)

                
                # WITHIN "WORDS", CREATE THE LIST OF GRAPHEME TOKENS
                # tr_g_layer: transcription string at graphic layer
                # sw_id: stringified word ID
                # g_tokens: a dictionary where:
                #   keys are grapheme token's sequential IDs in transcription
                #   values are grapheme type's IDs in sign table
                g_tokens = de_parenthesize(tr_g_layer,"(",")",sw_id)

                # CYCLE GRAPHEME TOKENS
                gl_print_end = '\n\t\t'
                # This is only useful to set the gl_print_end for last cycle
                g_id_suffix = 0
                for g_id in sorted(g_tokens):
                    g_id_suffix = g_id_suffix +1
                    # Print to graphic file
                    # g_id: the ID of each grapheme token in the transcription ("1.1", "1.2"...)
                    # g_ref: the REF linking to each grapheme type
                    #   in the grapheme table
                    g_ref = g_tokens[g_id]  # I'm adding this for code readability's sake
                    print('<g id="'+g_id+'" ref="#'+g_ref+'" />', file=g_xml)
                    # Align grapheme (at graphic layer) with a sequence of alphab. units
                    print('<link targets="salm_graphic.xml#'+g_id+' #'+g_id+'" />', file=ag_xml)
                    print('<ptr id="'+g_id+'" targets=\n\t\t"', sep='', end='', file=ag_xml)
                    if g_id_suffix == len(g_tokens):
                        gl_print_end = ''
                    # Add a new target to the ling./graph. intermediate pointer
                    print('salm_graphic.xml#'+g_id, sep='', end=gl_print_end, file=gl_xml)
                    
                    # RETRIEVE ALPHABETIC CONTENT(S) OF GRAPHEME TOKEN FROM GRAPHEME TABLE
                    # g_table[g_tokens[g_id]] = g_table[g_ref]: the list of all letters
                    #   (= letter IDs) corresponding to that grapheme
                    # a_id: each letter (= letter ID)
                    a_id_suffix = 0
                    ag_print_end = al_print_end = '\n\t\t'
                    for a_ref in g_table[g_ref]:
                        a_id_suffix = a_id_suffix +1
                        a_id = g_id+'.'+str(a_id_suffix)
                        # Print to alphabetic file
                        print('<g id="'+a_id+'" ref="#'+a_ref+'" />', file=a_xml)
                        # Add a new target to the graph./alph. intermediate pointer
                        if a_id_suffix == len(g_table[g_ref]):
                                ag_print_end = ''
                        print('salm_salm_alphabetic.xml#'+a_id, sep='', end=ag_print_end, file=ag_xml)
                        # Add a new target to the ling./alph. intermediate pointer
                        if a_id_suffix == len(g_table[g_ref]) and g_id_suffix == len(g_tokens):
                            al_print_end = ''
                        print('salm_alphabetic.xml#'+a_id, sep='', end=al_print_end, file=al_xml)
                        
                    # Close intermediate pointer in graph./alph. alignment file
                    print('" />\n', file=ag_xml)
                
                # Insert a new line (no longer a new "word"-SEG) in graphic
                # and in alphabetical files after a sequence of graphems that constitute
                # a word, for XML file readability's sake
                print('', file=g_xml)
                print('', file=a_xml)
                
                # Close intermediate pointer tag in linguistic/graph. alignment file
                print('" />\n', file=gl_xml)
                # Close intermediate pointer tag in linguistic/alph. alignment file
                print('" />\n', file=al_xml)

        # CLOSE ELEMENTS AT THE END OF XML FILES
        print('</text>\n</body>\n</TEI>', file=g_xml)
        print('</text>\n</body>\n</TEI>', file=a_xml)

        # CLOSE FILES
        g_xml.close()
        a_xml.close()
        l_xml.close()
        #lag_xml.close()
        al_xml.close()
        gl_xml.close()
        ag_xml.close()
        trf.close()

def menotify(transcription_file,graphemes_table,alphabemes_table):
        """ Transforms original transcription file into Menota TEI.
            The transcription file is a CSV in which:
            1) the column to the left has sequences of graphemes, arranged in lines
            (a line per word). This arrangement is meant to allow this script to
            insert interpretative SEGs marking what I think are words at the linguistic
            level(something that is not present in the MS),
            so I can later more easily align graphic transcription
            with linguistic transcription;
            2) the column to the right has inflected words at linguistic layer.
            3) the divider is a "§" key.
            4) in the left colum,
               c(u_)
            means that the SEG has two graphemes:
              a. the first has grapheme-reference "c";
              b. the second has grapheme-reference "u_"
    
        """


        # OPEN FILE TO WRITE TO
        xml = open('salm_menota.xml','w')

        # INPUT THE TWO TABLES OF SIGNS
        # At the moment, I don't need to input the table of signs/alphabemes as a dictionary. sgn5
        # g_table is a dictionary where:
            #   Keys: grapheme-IDs;
            #   values: lists (a_list) including all alphabetical-REFs
            # I'm ignoring split_g_expression right now
        g_table = read_table_of_signs(graphemes_table)

        # INPUT TRANSCRIPTION
        trf = open(transcription_file,'r')
        tr_rows = trf.readlines()

        # WRITE TABLE OF SIGNS/GRAPHEMES TO TEI HEADER
        print(charDecl(graphemes_table),file=xml) #sgn4
        #print(charDecl(alphabemes_table),file=xml)
                #sgn I have no clue where one could write this *second* table of signs
                # in the Menotified unique XML file

        # CYCLE WORDS IN TRANSCRIPTION
        # w_id: Sequential ID for any word in the transcription. It goes into
        #   <w id="1"> in the linguistic file
        w_id = 0
        for word in tr_rows:

            # INCREASE WORD COUNTER
            # As any line in the input file is a word in the MS, it creates a counter
            # for the TEI @id argument of the <w> element
            w_id = w_id + 1
            sw_id = str(w_id)   # This is simply a string corresponding to w_id (which is
                                # and integer). It is used to insert the ID in TEI/XML strings


            # SPLIT GRAPHEMATIC/LINGUISTIC LAYERS
            tr_g_layer, tr_l_layer = word.split('§')    # tr_g_layer = graphical layer transcription,
                                                    # tr_l_layer = linguistic layer transcription
            tr_g_layer = tr_g_layer.rstrip().lstrip()
            tr_l_layer = tr_l_layer.rstrip().lstrip()

            # NON-WORDS (LINE BREAK, WORD BREAK, PUNCTUATION)
            # At graphemic layer, check for 'special lines', like "-." (punctuation),
            # "-wb" ("word break", space) or "-lb" (line break). It's not necessary to
            # align with linguistic layer (as they are not words) nor with alphabetic
            # layer (as they do not have alphabetic content)
            if tr_g_layer == '-lb':  # Line break
                # This does not have any correspondence at the linguistic layer (so far)
                print('<lb id="'+sw_id+'" />\n', file=xml)
            elif tr_g_layer == '-wb':  # Word brak (proposal of TEI modification)
                # This does not have any correspondence at the linguistic layer (so far)
                # sgn: what's the Menota markup for this?
                print('<wb id="'+sw_id+'" />\n', file=xml)
            elif tr_g_layer == '-indent':  # Indent at beginning of line
                # This does not have any correspondence at the linguistic layer (so far)
                # sgn: what's the Menota markup for this?
                print('<indent id="'+sw_id+'" />\n', file=xml)
            elif tr_g_layer[0] == '-':  # Stand-alone (not in a word) TEI <g> element
                # This does not have any correspondence at the linguistic layer (so far)
                # sgn: Is there a TEI element for paragraphematic signs? Is it OK that a
                #   grapheme occurs outside a word?
                print('<g id="'+sw_id+'" ref="#grapheme_'+tr_g_layer.lstrip('-')+'" />\n', file=xml)
                g_ref = ''

            # REGULAR WORDS
            # If none of the previous 'special line'-cases applies, start a new word
            else:
                facs = ''       # Graphemic/me:facs transcription layer
                dipl = ''       # Alphabetic/me:dipl transcription layer
                align = ''      # Alphabetic-Graphemic alignment

                # Menota start tags (in variables)
                facs = facs + '\t<me:facs>\n'
                dipl = dipl + '\t<me:dipl>\n'

                
                # WITHIN "WORDS", CREATE THE LIST OF GRAPHEME TOKENS
                # tr_g_layer: transcription string at graphic layer
                # sw_id: stringified word ID
                # g_tokens: a dictionary where:
                #   keys are grapheme token's sequential IDs in transcription
                #   values are grapheme type's IDs in sign table
                g_tokens = de_parenthesize(tr_g_layer,"(",")",sw_id)

                # CYCLE GRAPHEME TOKENS
                gl_print_end = '\n\t\t'
                # This is only useful to set the gl_print_end for last cycle
                g_id_suffix = 0
                for g_id in sorted(g_tokens):
                    g_id_suffix = g_id_suffix +1
                    # Add to the facs variable (graphic layer)
                    # g_id: the ID of each grapheme token in the transcription ("1.1", "1.2"...)
                    # g_ref: the REF linking to each grapheme type
                    #   in the grapheme table
                    g_ref = g_tokens[g_id]  # I'm adding this for code readability's sake
                    facs = facs + '\t\t<g id="'+g_id+'" ref="#grapheme_'+g_ref+'" />\n'
                    # Align grapheme with a sequence of alphab. units
                    align = align + '\t<link targets="#'+g_id+' #ptr'+g_id+'" />\n'
                    align = align + '\t  <ptr id="ptr'+g_id+'" targets=\n\t\t"'
                    
                    if g_id_suffix == len(g_tokens):
                        gl_print_end = ''
                    
                    # RETRIEVE ALPHABETIC CONTENT(S) OF GRAPHEME TOKEN FROM GRAPHEME TABLE
                    # g_table[g_tokens[g_id]] = g_table[g_ref]: the list of all letters
                    #   (= letter IDs) corresponding to that grapheme
                    # a_id: each letter (= letter ID)
                    a_id_suffix = 0
                    ag_print_end = al_print_end = '\n\t\t'
                    for a_ref in g_table[g_ref]:
                        a_id_suffix = a_id_suffix +1
                        a_id = g_id+'.'+str(a_id_suffix)
                        # add to alphabetic/me:dipl transcription layer
                        dipl = dipl + '\t\t<g id="'+a_id+'" ref="#alphabeme_'+a_ref+'" />\n'
                        # Add a new target to the graph./alph. intermediate pointer
                        if a_id_suffix == len(g_table[g_ref]):
                                ag_print_end = ''
                        align = align + '#'+a_id+ag_print_end
                        # Add a new target to the ling./alph. intermediate pointer
                        if a_id_suffix == len(g_table[g_ref]) and g_id_suffix == len(g_tokens):
                            al_print_end = ''
                    # Close intermediate pointer in graph./alph. alignment
                    align = align + '" />\n'

                # As the word is over, close the <me:facs> and <me:dipl> tags
                facs = facs + '\t</me:facs>'
                dipl = dipl + '\t</me:dipl>'

                # PRINT THE ACTUAL STUFF TO THE salm_menota.xml FILE
                print('<w id="'+sw_id+'">', file=xml)
                # Print at graph./me:facs layer
                print(facs, file=xml)
                # Print at alph./me:dipl layer
                print(dipl, file=xml)
                # Print linguistic/me:norm layer
                print('\t<me:norm>\n\t\t'+tr_l_layer+'\n\t</me:norm>', file=xml)
                print(align, file=xml)
                print('</w>', file=xml)

        # CLOSE ELEMENTS AT THE END OF MENOTA XML FILE
        print('<text>\n<body>\n</TEI>', file=xml)

        # CLOSE FILES
        xml.close()
        #tbf.close()
        trf.close()

            
teify1("salmasianus.csv","salm_table_graphemes.csv","salm_table_alphabemes.csv")
menotify("salmasianus.csv","salm_table_graphemes.csv","salm_table_alphabemes.csv")
publish_by_products(".","/home/ilbuonme/siti/paolo.monella/lincei/files/edition")
