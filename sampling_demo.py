
import matplotlib.pylab as plt
import matplotlib.patches as ppa

from deephisto import Locations
from deephisto.image import ImageUtils
from deephisto.patch import PatchSampler



class PatchSamplingDemo:

    def __init__(self,locations):
        self.utils = ImageUtils(locations)
        self.subject = None
        self.index   = None
        self.mask    = None
        self.bmask   = None
        self.fig     = None
        self.ax      = None
        self.sampler = None

    def configure(self,subject,index, sampler):
        """
        subject: one of the deephisto subjects
        index: one of the slices (needs to be anotated so the png exists)

        """
        self.subject = subject
        self.index = index
        self.utils.set_subject(subject)
        self.mask = self.utils.load_mask_png(index)
        self.bmask = self.utils.get_binary_mask(index)
        self.sampler = sampler
        self.sampler.set_mask(self.bmask)

    def show_rectangle(self, x, y):
        '''
        Draws and initializes a draggable rectangle
        '''
        WSIDE = self.sampler.WSIDE
        WSIZE = self.sampler.WSIZE
        rect = ppa.Rectangle((y - WSIDE, x - WSIDE), WSIZE, WSIZE,
                             linewidth=1, edgecolor='r', facecolor='r', alpha=0.2)
        self.ax.add_patch(rect)
        plt.pause(0.001)

    def run(self):
        """
        Shows the sampling mechanism in action

        """
        print
        print
        print 'DEMO START'
        print '----------------------'
        print ' Subject : %s'%self.subject
        print ' Slice   : %d'%self.index


        fig, ax = plt.subplots(1, facecolor='black')
        self.fig = fig
        self.ax = ax

        fig.canvas.set_window_title('DeepHisto: patch sampling demo')
        ax.set_axis_bgcolor('black')
        ax.imshow(self.mask, alpha=0.5)
        plt.draw()


        self.sampler.sample()

        plt.show()
        print '----------------------'
        print 'DEMO END'


if __name__=='__main__':
    locations = Locations('/home/dcantor/projects/deephisto')
    demo = PatchSamplingDemo(locations)
    demo.configure('EPI_P036',7)
    demo.run()