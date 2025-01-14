import pandas as pd
import spacy
import difflib
from spacy import displacy
from difflib import get_close_matches
df=pd.read_csv("Augmented_Non_Complex.csv")
l=df.values.tolist()
def give_column(sen_without_ne):
    column_names=['Place','Affiliate','AffiliationID','AuthID','FieldID','Name','ConfID','PaperID','Venue','Year','Topic','KeywordID','Summary','Title']
    lower_column_names=[]
    for i in column_names:
        lower_column_names.append(i.lower())
    nlp = spacy.load("en_core_web_sm")
    doc=nlp(sen_without_ne.lower())
    l=[token.text for token in doc if (token.pos_ == "NOUN" or token.pos_=="PROPN" or token.pos_=="VERB")]
    # print(l)
    a=[]
    x=[]
    for i in l:
        if len(i)>8:
            x=get_close_matches(i[:4].lower(), lower_column_names,n=1,cutoff=0.55)
        else:
            x=get_close_matches(i.lower(), lower_column_names,n=1,cutoff=0.55)
        if not x==[]:
            for j in range(len(lower_column_names)):
                if lower_column_names[j]==x[0]:
                    a.append([column_names[j],difflib.SequenceMatcher(None, i, lower_column_names[j]).ratio()])
                    break
                else:
                    continue
        # else:
        #     print('error')
    z=[ele[0] for ele in sorted(a,key=lambda x:x[1],reverse=1)]
    znew=[z[0]]
    for i in range(1,len(z)):
        if not z[i] in z[:i]:
            znew.append(z[i])
    return znew