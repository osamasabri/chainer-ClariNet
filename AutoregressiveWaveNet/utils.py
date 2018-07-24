import random
import pathlib

import numpy
import librosa
import chainer


class Preprocess(object):
    def __init__(self, sr, n_fft, hop_length, n_mels, top_db,
                 length, categorical_output_dim):
        self.sr = sr
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.n_mels = n_mels
        self.top_db = top_db

        if length is None:
            self.length = None
        else:
            self.length = length + 1
        if categorical_output_dim is False or categorical_output_dim is None:
            self.output_dim = 1
        else:
            self.output_dim = categorical_output_dim

    def __call__(self, path):
        # load data(trim and normalize)
        raw, _ = librosa.load(path, self.sr)
        raw, _ = librosa.effects.trim(raw, self.top_db)
        raw /= numpy.abs(raw).max()
        raw = raw.astype(numpy.float32)

        # padding/triming
        if self.length is not None:
            if len(raw) <= self.length:
                # padding
                pad = self.length - len(raw)
                raw = numpy.concatenate(
                    (raw, numpy.zeros(pad, dtype=numpy.float32)))
            else:
                # triming
                start = random.randint(0, len(raw) - self.length - 1)
                raw = raw[start:start + self.length]

        # make mel spectrogram
        spectrogram = librosa.feature.melspectrogram(
            raw, self.sr, n_fft=self.n_fft, hop_length=self.hop_length,
            n_mels=self.n_mels)
        spectrogram = librosa.power_to_db(
            spectrogram, ref=numpy.max)
        spectrogram += 80
        spectrogram /= 80
        if self.length is not None:
            spectrogram = spectrogram[:, :self.length // self.hop_length]
        spectrogram = spectrogram.astype(numpy.float32)

        # expand dimensions
        raw = numpy.expand_dims(raw, 0)  # expand channel
        raw = numpy.expand_dims(raw, -1)  # expand height
        spectrogram = numpy.expand_dims(spectrogram, 0)

        if self.output_dim == 1:
            return raw[:, :-1], spectrogram, raw[:, 1:]
        else:
            quantized_values = \
                numpy.arange(self.output_dim) * 2 / self.output_dim - 1
            digitized_values = numpy.digitize(raw, quantized_values)
            return raw[:, :-1], spectrogram, digitized_values[:, 1:]


# class Logistic(chainer.distribution.Distribution.Normal):

#     def broadcast_to(self, x, shape):
#         return chainer.functions.array.broadcast.broadcast_to(x, shape)

#     def cdf(self, x):
#         return chainer.functions.sigmoid(
#             self.broadcast_to(
#                 chainer.functions.exp(-self.log_scales), x.shape) *
#             (self.broadcast_to(self.loc, x.shape) - x))

#     def entropy(self):
#         return self.log_scales + 2

#     def icdf(self, x):

#     def log_prob(self, x):

#     def prob(self, x):

#     def sample_n(self, x):

#     @property
#     def stddev(self):

#     def survival_function(self, x):

#     def variance(self):


def get_LJSpeech_paths(root):
    filepaths = sorted([
        str(path) for path in pathlib.Path(root).glob('wavs/*.wav')])
    metadata_path = pathlib.Path(root).joinpath('metadata.csv')
    return filepaths, metadata_path


def get_VCTK_paths(root):
    filepaths = sorted([
        str(path) for path in pathlib.Path(root).glob('wav48/*/*.wav')])
    metadata_paths = sorted([
        str(path) for path in pathlib.Path(root).glob('txt/*/*.txt')])
    return filepaths, metadata_paths
