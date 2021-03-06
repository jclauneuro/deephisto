from subjects import dh_load_subjects
from deephisto import PatchSampler, PatchCreator, Locations, ImageUtils


def _get_slices(locations):
    slices = {}
    utils = ImageUtils(locations)
    subjects = dh_load_subjects()
    print
    print 'List of subjects [slices] that will be used for patch creation'
    print '--------------------------------------------------------------'
    for s in subjects:
        utils.set_subject(s)
        slices[s] = utils.get_annotation_indices()
        print s, slices[s]

    return slices


def dh_create_patches(target_dir, slices, locations):

    msampler = PatchSampler(wsize=28, type=PatchSampler.TYPE_MONTECARLO,
                           params=dict(coverage=0.8))

    bsampler = PatchSampler(wsize=28, type=PatchSampler.TYPE_BACKGROUND,
                      params=dict(overlap_factor=2, xmax=3, ymax=3))

    utils = ImageUtils(locations)

    mcreator = PatchCreator(utils, msampler, target_dir)
    bcreator = PatchCreator(utils, bsampler, target_dir)

    mcreator.clear_dir(True)

    for subject in sorted(slices):
        indices  = slices[subject]
        for index in indices:
            mcreator.create_patches(subject, index)
            bcreator.create_patches(subject, index)


if __name__ == '__main__':
    locations = Locations('/home/dcantor/projects/deephisto')
    slices = _get_slices(locations)
    dh_create_patches('28x28b', slices, locations)
