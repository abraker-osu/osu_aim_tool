from pyqtgraph import PlotItem


def plot_csv_export(self, fileName=None):
    
    if not isinstance(self.item, PlotItem):
        raise Exception("Must have a PlotItem selected for CSV export.")
    
    if fileName is None:
        self.fileSaveDialog(filter=["*.csv", "*.tsv"])
        return

    data = []
    header = []

    appendAllX = self.params['columnMode'] == '(x,y) per plot'

    for i, c in enumerate(self.item.curves):
        cd = c.getData()
        
        if cd[0] is None:
            continue

        data.append(cd)

        if hasattr(c, 'implements') and c.implements('plotData') and c.name() is not None:
            name = c.name().replace('"', '""') + '_'
            xName, yName = '"'+name+'x"', '"'+name+'y"'
        else:
            xName = 'x%04d' % i
            yName = 'y%04d' % i

        if appendAllX or i == 0:
            header.extend([xName, yName])
        else:
            header.extend([yName])

    if len(data) == 0:
        # No data
        return

    if self.params['separator'] == 'comma':
        sep = ','
    else:
        sep = '\t'

    with open(fileName, 'w', encoding='utf-8') as fd:
        fd.write(sep.join(map(str, header)) + '\n')
        
        i = 0
        numFormat = '%%0.%dg' % self.params['precision']
        numRows = max([len(d[0]) for d in data])

        for i in range(numRows):
            for j, d in enumerate(data):
                # write x value if this is the first column, or if we want
                # x for all rows
                if appendAllX or j == 0:
                    if d is not None and i < len(d[0]):
                        fd.write(numFormat % d[0][i] + sep)
                    else:
                        fd.write(' %s' % sep)

                # write y value
                if d is not None and i < len(d[1]):
                    fd.write(numFormat % d[1][i] + sep)
                else:
                    fd.write(' %s' % sep)

            fd.write('\n')
