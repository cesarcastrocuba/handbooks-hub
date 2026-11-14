"""Generate living style-guide data from the canonical design contract."""
from . import design
from .portal_markup import resource, template


def design_page() -> str:
    tokens = design.load_tokens()
    colors = ['| Role | Light | Dark | Print |', '| --- | --- | --- | --- |']
    colors += [f'| `{name}` | ' + ' | '.join(template('swatch.html',color=values[scheme]).strip()+f' `{values[scheme]}`' for scheme in design.SCHEMES) + ' |'
               for name,values in tokens['color'].items()]
    contrast = ['| Pair | Scheme | Ratio | Minimum |', '| --- | --- | --- | --- |']
    for pair in tokens['contrast']:
        for scheme in pair['schemes']:
            ratio = design.contrast_ratio(tokens['color'][pair['foreground']][scheme], tokens['color'][pair['background']][scheme])
            contrast.append(f'| {pair["name"]} | {scheme} | {ratio:.2f}:1 | {pair["minimum"]}:1 |')
    for name, role in tokens['callout'].items():
        for scheme in ('light','dark'):
            ratio = design.contrast_ratio(role['accent'][scheme], role['tint'][scheme])
            contrast.append(f'| {name} title on tint | {scheme} | {ratio:.2f}:1 | {design.MINIMUM_TEXT_CONTRAST}:1 |')
    types=['| Role | Family | Web size | Line height |', '| --- | --- | --- | --- |']
    for name in ('body','display','code'):
        role=tokens['type'][name]
        types.append(f'| {name} | {role["web_family"]} | {role["web_size_px"]} px | {role["line_height"]} |')
    callouts=[]
    for name in tokens['callout']:
        classes='.callout-note .review' if name=='review' else '.callout-'+name
        callouts.append(f'::: {{{classes} appearance="simple" icon=false title="{name.title()}"}}\nA {name} callout uses its shared accent and tint.\n:::')
    page=resource('design.qmd')
    for key,lines in [('colors',colors),('contrast',contrast),('type',types),('callouts',callouts)]:
        page=page.replace('{{'+key+'}}','\n\n'.join(lines) if key=='callouts' else '\n'.join(lines))
    return page
