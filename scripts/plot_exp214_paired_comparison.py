"""Plot measured paired CV, preserving embryo and uncertainty limitations."""
import argparse,json,os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR',str(Path('.tmp/matplotlib_exp214').resolve()))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def main():
    p=argparse.ArgumentParser();p.add_argument('--comparison',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    d=json.loads(a.comparison.read_text());assert d['status']=='PASS_PAIRED_COMPARISON'
    epochs=d.get('training_epochs',12)
    keys=['EXP209_frozen','public','local'];labels=['Прежний EXP209',f'Публичный граф · refit{epochs}','Наш граф · те же детекции'];colors=['#87919b','#d18331','#237d70']
    fig,(ax,bx)=plt.subplots(1,2,figsize=(12.5,5.7),gridspec_kw={'width_ratios':[1.45,1]})
    x=np.arange(3);width=.23
    for i,(k,label,color) in enumerate(zip(keys,labels,colors)):
        vals=[d['scores'][k],d['by_embryo'][k]['44b6'],d['by_embryo'][k]['6bba']]
        bars=ax.bar(x+(i-1)*width,vals,width,color=color,label=label)
        ax.bar_label(bars,labels=[f'{v:.3f}' for v in vals],fontsize=8,padding=3)
    ax.set_xticks(x,['Pooled','Target 44b6','Target 6bba']);ax.set_ylim(0,1.02);ax.set_ylabel('Официальный tracking score');ax.legend(loc='upper left',fontsize=8,frameon=False);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
    contrasts=[]
    for ref,label in [('public','Наш граф − публичный'),('EXP209_frozen','Наш граф − прежний EXP209')]:
        q=next(r for r in d['comparisons'] if {r['a'],r['b']}=={'local',ref});sign=1 if q['a']=='local' else -1
        delta=sign*q['delta'];lo,hi=sorted(sign*v for v in q['movie_stratified_delta_interval_95']);contrasts.append((label,delta,lo,hi))
    for i,(label,delta,lo,hi) in enumerate(contrasts):
        bx.errorbar(delta,i,xerr=[[delta-lo],[hi-delta]],fmt='o',color='#237d70',capsize=5,lw=2)
        bx.annotate(f'{delta:+.4f}\n[{lo:+.4f}; {hi:+.4f}]',(delta,i),xytext=(0,15),textcoords='offset points',ha='center',fontsize=9)
    bx.set_yticks(range(len(contrasts)),[r[0] for r in contrasts],fontsize=9);bx.axvline(0,color='#8f969d',lw=1);bx.set_ylim(-.5,1.7);bx.set_xlabel('Разница pooled score · условный 95% интервал');bx.grid(axis='x',alpha=.15)
    for plot in (ax,bx):
        plot.spines[['top','right']].set_visible(False)
    fig.suptitle(f'EXP214: парное сравнение на {d["movies"]} роликах',fontsize=16,x=.06,ha='left')
    fig.text(.06,.055,f'Два исключаемых эмбриона; bootstrap по роликам не оценивает неопределённость новых эмбрионов.\nRefit{epochs} — новое обучение, а не честный OOF опубликованных весов с LB 0.946.',fontsize=9,color='#525b64')
    fig.tight_layout(rect=[0,.13,1,.94]);a.output.parent.mkdir(parents=True,exist_ok=True)
    for ext in ('png','svg'):fig.savefig(a.output.with_suffix('.'+ext),dpi=160,bbox_inches='tight')
    plt.close(fig)
if __name__=='__main__':main()
