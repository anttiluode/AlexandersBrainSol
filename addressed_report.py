"""Descriptive addressed-array report; consumes locked metrics without tuning."""
import argparse,gzip,json
from pathlib import Path
import numpy as np
import addressed_updates as au
from addressed_audit import load_seed


def analysis(directory):
    directory=Path(directory);manifest=json.loads((directory/'manifest.json').read_text())
    rows=[load_seed(directory,entry) for entry in manifest['rows']]
    ordinary={}
    for arm in au.ARMS:
        events=[e for row in rows for e in row['arms'][arm]['events']]
        ordinary[arm]={k:float(np.mean([np.mean(e['ordinary'][k]) for e in events])) for k in ['writes','whole_array','voted_read','bystander_survival','read_survival']}
    return dict(source_commit=manifest['source_commit'],mode=manifest['mode'],seeds=manifest['seeds'],
                histories=6*len(rows),updates=24*len(rows),bystander_exposures=48*len(rows),
                queries=6*4*3*5*len(rows),ring=manifest['result'],ordinary=ordinary,
                refinement={k:v for k,v in manifest['refinement'].items() if k!='checks'}),rows


def markdown(r):
    text=['# Selective updates in a three-cell memory array','',f"Mode: **{r['mode']}**. Locked source: `{r['source_commit']}`.",
          f"{len(r['seeds'])} independent noise-seed batches, {r['histories']} three-cell histories, {r['updates']} requested updates, {r['bystander_exposures']} bystander exposures per arm.",'',
          '| Ring controller | Correct exclusive route | Written before read | Bystanders survive | Whole array correct | Voted read of intended contents | Operational gate |',
          '| --- | ---: | ---: | ---: | ---: | ---: | --- |']
    for name in au.ARMS:
        s=r['ring']['summaries'][name]
        values=' | '.join(f'{100*s[k]:.2f}%' for k in ['routing','writes','bystander_survival','whole_array','voted_read'])
        text.append(f"| {name} | {values} | {'PASS' if r['ring']['operational'][name]['pass'] else 'FAIL'} |")
    b=r['ring']['analog_benefit']
    text += ['',f"**Analog-state benefit gate: {'PASS' if b['pass'] else 'FAIL'}.** Whole-array difference trace minus snapped latch = {100*b['whole_array_gain']:.2f} percentage points; positive seed fraction {100*b['positive_seed_fraction']:.1f}%.",'',
             'The snapped decision depends only on a three-state address through the delay, encodable in two bits; actual storage uses an integer. Diagnostic cue and trace arrays are also computed and archived outside that decision path. This is an information-sufficiency control, not a physically packed two-bit implementation. Both controllers share a three-float cue accumulator and a trigger marker. The analog controller keeps integrating background activity during the delay. These policies are engineered. Neither learns an address mapping or the command value.', '',
             '| Ordinary three-well array | Written before read | Bystanders survive | Whole array correct | Voted read |',
             '| --- | ---: | ---: | ---: | ---: |']
    for name,s in r['ordinary'].items():
        text.append('| '+name+' | '+' | '.join(f'{100*s[k]:.2f}%' for k in ['writes','bystander_survival','whole_array','voted_read'])+' |')
    text += ['', 'Independent cells share a broadcast write bias; there is no physical inter-cell coupling. Ordinary and ring media have unmatched energy, dimensionality and microscopic noise. No topology, efficiency or general learning advantage follows.', '',
             f"Read accuracy has {r['queries']//5} cell-event votes per arm, from {r['queries']} individual queries. This is five-query accuracy, not single-query accuracy. All event endpoints stay in the denominator, including consequences of earlier failed writes. Bystander survival rejects any stepwise departure or invalidity, even if the integer later returns. Readout uses five noisy local queries and a strict symbol majority; abstentions count wrong. Controllers see no field, reader output or scoring oracle.", '',
             'Numerical check: '+json.dumps(r['refinement'],sort_keys=True)+'. One canonical history covers the entire repeated sequence and all arms; this is a sampled check.', '',
             'The externally generated request supplies content. Spatial cue ports supply the address convention; learning where an object belongs remains untested. The result concerns access and reuse of a finite memory component.', '']
    return '\n'.join(text)


def figure(rows,path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap,BoundaryNorm
    from matplotlib.patches import Rectangle
    row=rows[0];old=np.asarray(row['initial'])
    goal=np.stack([old]+[np.asarray(e['goal']) for e in row['arms']['oracle']['events']],axis=-1).reshape(18,5)
    arrays=[goal]
    for arm in ['trace','snap']:
        arrays.append(np.stack([old]+[np.asarray(e['final']) for e in row['arms'][arm]['events']],axis=-1).reshape(18,5))
    cmap=ListedColormap(['#4477aa','#eeeeee','#ee9933']);norm=BoundaryNorm([-1.5,-.5,.5,1.5],3)
    fig,axes=plt.subplots(1,3,figsize=(10,9),sharey=True,constrained_layout=True)
    for ax,data,title in zip(axes,arrays,['Commanded contents','Analog address trace','Snapped address latch']):
        ax.imshow(data,cmap=cmap,norm=norm,aspect='auto')
        for h in range(6):
            if h:ax.axhline(3*h-.5,color='white',lw=3)
        for y in range(18):
            for x in range(5):
                ax.text(x,y,str(data[y,x]),ha='center',va='center',fontsize=9)
                if data[y,x]!=goal[y,x]:ax.add_patch(Rectangle((x-.46,y-.46),.92,.92,fill=False,edgecolor='#bb2233',lw=2))
        ax.set_xticks(range(5),['Initial','1','2','3','4']);ax.set_xlabel('Update event');ax.set_title(title,fontsize=11)
    axes[0].set_yticks(range(18),[f'H{h} / {c}' for h in range(6) for c in ['A','B','C']]);axes[0].set_ylabel('History / cell')
    fig.suptitle(f"First locked {row['seed']} noise batch — all six histories\nWinding: blue −1, grey 0, orange +1; red outline = mismatch",fontsize=12)
    fig.savefig(path,dpi=170);plt.close(fig)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('directory');parser.add_argument('--output-dir',required=True);args=parser.parse_args()
    directory=Path(args.output_dir);directory.mkdir(exist_ok=False,parents=True)
    r,rows=analysis(args.directory)
    (directory/'report.json').write_text(json.dumps(r,indent=2)+'\n')
    (directory/'report.md').write_text(markdown(r)+'\n![All six histories in the first fresh batch](array.png)\n')
    figure(rows,directory/'array.png');print(json.dumps(r['ring'],indent=2))

if __name__=='__main__':main()
