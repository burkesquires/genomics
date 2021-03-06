#     FASTQFile.py: read and manipulate FASTQ files and data
#     Copyright (C) University of Manchester 2012-13 Peter Briggs
#
########################################################################
#
# FASTQFile.py
#
#########################################################################

__version__ = "0.2.1"

"""FASTQFile

Implements a set of classes for reading through FASTQ files and manipulating
the data within them:

* FastqIterator: enables looping through all read records in FASTQ file
* FastqRead: provides access to a single FASTQ read record

Information on the FASTQ file format: http://en.wikipedia.org/wiki/FASTQ_format
"""

#######################################################################
# Import modules that this module depends on
#######################################################################
from collections import Iterator
import os
import re
import logging
import gzip

#######################################################################
# Constants/globals
#######################################################################

# Regular expression to match an "ILLUMINA18" format sequence identifier
# i.e. Illumina 1.8+
# @EAS139:136:FC706VJ:2:2104:15343:197393 1:Y:18:ATCACG
ILLUMINA18_SEQID = re.compile(r"^@([^\:]+):([^\:]+):([^\:]+):([^\:]+):([^\:]+):([^\:]+):([^ ]+) ([^\:]+):([^\:]+):([^\:]+):([^\:]*)$")

# Regular expression to match a "ILLUMINA" format sequence identifier
# i.e. Illumina 1.3+, 1.5+
# @HWUSI-EAS100R:6:73:941:1973#0/1
ILLUMINA_SEQID = re.compile(r"^@([^\:]+):([^\:]+):([^\:]+):([^\:]+):([^\#]+)#([^/])/(.+)$")

#######################################################################
# Class definitions
#######################################################################

class FastqIterator(Iterator):
    """FastqIterator

    Class to loop over all records in a FASTQ file, returning a FastqRead
    object for each record.

    Example looping over all reads
    >>> for read in FastqIterator(fastq_file):
    >>>    print read

    Input FASTQ can be in gzipped format; FASTQ data can also be supplied
    as a file-like object opened for reading, for example
    >>> fp = open(fastq_file,'rU')
    >>> for read in FastqIterator(fp=fp):
    >>>    print read
    >>> fp.close()

    """

    def __init__(self,fastq_file=None,fp=None):
        """Create a new FastqIterator

        The input FASTQ can be either a text file or a compressed (gzipped)
        FASTQ, specified via a file name (using the 'fastq' argument), or a
        file-like object opened for line reading (using the 'fp' argument).

        Arguments:
           fastq_file: name of the FASTQ file to iterate through
           fp: file-like object opened for reading

        """
        self.__fastq_file = fastq_file
        if fp is None:
            if os.path.splitext(self.__fastq_file)[1] == '.gz':
                self.__fp = gzip.open(self.__fastq_file,'r')
            else:
                self.__fp = open(self.__fastq_file,'rU')
        else:
            self.__fp = fp

    def next(self):
        """Return next record from FASTQ file as a FastqRead object
        """
        seqid_line = self.__fp.readline()
        seq_line = self.__fp.readline()
        optid_line = self.__fp.readline()
        quality_line = self.__fp.readline()
        if quality_line != '':
            return FastqRead(seqid_line,seq_line,optid_line,quality_line)
        else:
            # Reached EOF
            if self.__fastq_file is None:
                self.__fp.close()
            raise StopIteration

class FastqRead:
    """Class to store a FASTQ record with information about a read

    Provides the following properties:

    seqid: the "sequence identifier" information (first line of the read record)
      as a SequenceIdentifier object
    sequence: the raw sequence (second line of the record)
    optid: the optional sequence identifier line (third line of the record)
    quality: the quality values (fourth line of the record)
    """

    def __init__(self,seqid_line=None,seq_line=None,optid_line=None,quality_line=None):
        """Create a new FastqRead object

        Arguments:
          seqid_line: first line of the read record
          sequence: second line of the record
          optid: third line of the record
          quality: fourth line of the record
        """
        self.__raw_attributes = {}
        self.__raw_attributes['seqid'] = seqid_line
        self.sequence = str(seq_line).strip()
        self.optid = str(optid_line.strip())
        self.quality = str(quality_line.strip())

    @property
    def seqid(self):
        if 'seqid' in self.__raw_attributes:
            self._seqid = SequenceIdentifier(self.__raw_attributes['seqid'])
            del(self.__raw_attributes['seqid'])
        return self._seqid

    def __repr__(self):
        return '\n'.join((str(self.seqid),
                          self.sequence,
                          self.optid,
                          self.quality))

class SequenceIdentifier:
    """Class to store/manipulate sequence identifier information from a FASTQ record

    Provides access to the data items in the sequence identifier line of a FASTQ
    record.
    """

    def __init__(self,seqid):
        """Create a new SequenceIdentifier object

        Arguments:
          seqid: the sequence identifier line (i.e. first line) from the
            FASTQ read record
        """
        self.__seqid = str(seqid).strip()
        self.format = None
        # There are at least two variants of the sequence id line, this is an
        # example of Illumina 1.8+ format:
        # @EAS139:136:FC706VJ:2:2104:15343:197393 1:Y:18:ATCACG
        # The alternative is Illumina:
        # @HWUSI-EAS100R:6:73:941:1973#0/1
        illumina18 = ILLUMINA18_SEQID.match(self.__seqid)
        illumina = ILLUMINA_SEQID.match(self.__seqid)
        if illumina18:
            self.format = 'illumina18'
            self.instrument_name = illumina18.group(1)
            self.run_id = illumina18.group(2)
            self.flowcell_id = illumina18.group(3)
            self.flowcell_lane = illumina18.group(4)
            self.tile_no = illumina18.group(5)
            self.x_coord = illumina18.group(6)
            self.y_coord = illumina18.group(7)
            self.multiplex_index_no = None
            self.pair_id = illumina18.group(8)
            self.bad_read = illumina18.group(9)
            self.control_bit_flag = illumina18.group(10)
            self.index_sequence = illumina18.group(11)
        elif illumina:
            self.format = 'illumina'
            self.instrument_name = illumina.group(1)
            self.run_id = None
            self.flowcell_id = None
            self.flowcell_lane = illumina.group(2)
            self.tile_no = illumina.group(3)
            self.x_coord = illumina.group(4)
            self.y_coord = illumina.group(5)
            self.multiplex_index_no = illumina.group(6)
            self.pair_id = illumina.group(7)
            self.bad_read = None
            self.control_bit_flag = None
            self.index_sequence = None
        
    def __repr__(self):
        if self.format == 'illumina18':
            return "@%s:%s:%s:%s:%s:%s:%s %s:%s:%s:%s" % (self.instrument_name, 
                                                          self.run_id,
                                                          self.flowcell_id,
                                                          self.flowcell_lane,
                                                          self.tile_no,
                                                          self.x_coord,
                                                          self.y_coord,
                                                          self.pair_id,
                                                          self.bad_read,
                                                          self.control_bit_flag,
                                                          self.index_sequence)
        elif self.format == 'illumina':
            return "@%s:%s:%s:%s:%s#%s/%s" % (self.instrument_name,
                                              self.flowcell_lane,
                                              self.tile_no,
                                              self.x_coord,
                                              self.y_coord,
                                              self.multiplex_index_no,
                                              self.pair_id)
        else:
            # Return what was put in
            return self.__seqid

#######################################################################
# Functions
#######################################################################

def nreads(fastq=None,fp=None):
    """Return number of reads in a FASTQ file

    Performs a simple-minded read count, by counting the number of lines
    in the file and dividing by 4.

    The FASTQ file can be specified either as a file name (using the 'fastq'
    argument) or as a file-like object opened for line reading (using the
    'fp' argument).

    This function can handle gzipped FASTQ files supplied via the 'fastq'
    argument.

    Line counting uses a variant of the "buf count" method outlined here:
    http://stackoverflow.com/a/850962/579925

    Arguments:
      fastq: fastq(.gz) file
      fp: open file descriptor for fastq file

    Returns:
      Number of reads

    """
    nlines = 0
    if fp is None:
        if os.path.splitext(fastq)[1] == '.gz':
            fp = gzip.open(fastq)
        else:
            fp = open(fastq)
    buf_size = 1024 * 1024
    read_fp = fp.read # optimise the loop
    buf = read_fp(buf_size)
    while buf:
        nlines += buf.count('\n')
        buf = read_fp(buf_size)
    if fastq is not None:
        fp.close()
    if (nlines%4) != 0:
        raise Exception,"Bad read count (not fastq file, or corrupted?)"
    return nlines/4

#######################################################################
# Tests
#######################################################################

import unittest
import cStringIO

fastq_data = """@73D9FA:3:FC:1:1:7507:1000 1:N:0:
NACAACCTGATTAGCGGCGTTGACAGATGTATCCAT
+
#))))55445@@@@@C@@@@@@@@@:::::<<:::<
@73D9FA:3:FC:1:1:15740:1000 1:N:0:
NTCTTGCTGGTGGCGCCATGTCTAAATTGTTTGGAG
+
#+.))/0200<<<<<:::::CC@@C@CC@@@22@@@
@73D9FA:3:FC:1:1:8103:1000 1:N:0:
NGACCGATTAGAGGCGTTTTATGATAATCCCAATGC
+
#(,((,)*))/.0--2255282299@@@@@@@@@@@
@73D9FA:3:FC:1:1:7488:1000 1:N:0:
NTGATTGTCCAGTTGCATTTTAGTAAGCTCTTTTTG
+
#,,,,33223CC@@@@@@@C@@@@@@@@C@CC@222
@73D9FA:3:FC:1:1:6680:1000 1:N:0:
NATAAATCACCTCACTTAAGTGGCTGGAGACAAATA
+
#--,,55777@@@@@@@CC@@C@@@@@@@@:::::<
"""

class TestFastqIterator(unittest.TestCase):
    """Tests of the FastqIterator class
    """

    def test_fastq_iterator(self):
        """Check iteration over small FASTQ file
        """
        fp = cStringIO.StringIO(fastq_data)
        fastq = FastqIterator(fp=fp)
        nreads = 0
        fastq_source = cStringIO.StringIO(fastq_data)
        for read in fastq:
            nreads += 1
            self.assertTrue(isinstance(read.seqid,SequenceIdentifier))
            self.assertEqual(str(read.seqid),fastq_source.readline().rstrip('\n'))
            self.assertEqual(read.sequence,fastq_source.readline().rstrip('\n'))
            self.assertEqual(read.optid,fastq_source.readline().rstrip('\n'))
            self.assertEqual(read.quality,fastq_source.readline().rstrip('\n'))
        self.assertEqual(nreads,5)

class TestFastqRead(unittest.TestCase):
    """Tests of the FastqRead class
    """

    def test_fastqread(self):
        """Check FastqRead stores input correctly
        """
        seqid = "@HWI-ST1250:47:c0tr3acxx:4:1101:1283:2323 1:N:0:ACAGTGATTCTTTCCC\n"
        seq = "GGTGTCTTCAAAAAGGCCAACCAGATAGGCCTCACTTGCCTCCTGCAAAGCACCGATAGCTGCGCTCTGGAAGCGCAGATCTGTTTTAAAGTCCTGAGCAA\n"
        optid = "+\n"
        quality = "=@@D;DDFFHDHHIJIIIIIIGIGIGDIHGGEIGICFGIGHIIGII@?FGIGIEI@EHEFFEEBAACD;@ACCDDBDBDDACCC3>CD>:ADCCDDD?C@\n"
        read = FastqRead(seqid,seq,optid,quality)
        self.assertTrue(isinstance(read.seqid,SequenceIdentifier))
        self.assertEqual(str(read.seqid),seqid.rstrip('\n'))
        self.assertEqual(read.sequence,seq.rstrip('\n'))
        self.assertEqual(read.optid,optid.rstrip('\n'))
        self.assertEqual(read.quality,quality.rstrip('\n'))

class TestSequenceIdentifier(unittest.TestCase):
    """Tests of the SequenceIdentifier class
    """

    def test_read_illumina18_id(self):
        """Process an 'illumina18'-style sequence identifier
        """
        seqid_string = "@EAS139:136:FC706VJ:2:2104:15343:197393 1:Y:18:ATCACG"
        seqid = SequenceIdentifier(seqid_string)
        # Check we get back what we put in
        self.assertEqual(str(seqid),seqid_string)
        # Check the format
        self.assertEqual('illumina18',seqid.format)
        # Check attributes were correctly extracted
        self.assertEqual('EAS139',seqid.instrument_name)
        self.assertEqual('136',seqid.run_id)
        self.assertEqual('FC706VJ',seqid.flowcell_id)
        self.assertEqual('2',seqid.flowcell_lane)
        self.assertEqual('2104',seqid.tile_no)
        self.assertEqual('15343',seqid.x_coord)
        self.assertEqual('197393',seqid.y_coord)
        self.assertEqual('1',seqid.pair_id)
        self.assertEqual('Y',seqid.bad_read)
        self.assertEqual('18',seqid.control_bit_flag)
        self.assertEqual('ATCACG',seqid.index_sequence)

    def test_read_illumina18_id_no_index_sequence(self):
        """Process an 'illumina18'-style sequence id with no index sequence (barcode)
        """
        seqid_string = "@73D9FA:3:FC:1:1:7507:1000 1:N:0:"
        seqid = SequenceIdentifier(seqid_string)
        # Check we get back what we put in
        self.assertEqual(str(seqid),seqid_string)
        # Check the format
        self.assertEqual('illumina18',seqid.format)
        # Check attributes were correctly extracted
        self.assertEqual('73D9FA',seqid.instrument_name)
        self.assertEqual('3',seqid.run_id)
        self.assertEqual('FC',seqid.flowcell_id)
        self.assertEqual('1',seqid.flowcell_lane)
        self.assertEqual('1',seqid.tile_no)
        self.assertEqual('7507',seqid.x_coord)
        self.assertEqual('1000',seqid.y_coord)
        self.assertEqual('1',seqid.pair_id)
        self.assertEqual('N',seqid.bad_read)
        self.assertEqual('0',seqid.control_bit_flag)
        self.assertEqual('',seqid.index_sequence)        

    def test_read_illumina_id(self):
        """Process an 'illumina'-style sequence identifier
        """
        seqid_string = "@HWUSI-EAS100R:6:73:941:1973#0/1"
        seqid = SequenceIdentifier(seqid_string)
        # Check we get back what we put in
        self.assertEqual(str(seqid),seqid_string)
        # Check the format
        self.assertEqual('illumina',seqid.format)
        # Check attributes were correctly extracted
        self.assertEqual('HWUSI-EAS100R',seqid.instrument_name)
        self.assertEqual('6',seqid.flowcell_lane)
        self.assertEqual('73',seqid.tile_no)
        self.assertEqual('941',seqid.x_coord)
        self.assertEqual('1973',seqid.y_coord)
        self.assertEqual('0',seqid.multiplex_index_no)
        self.assertEqual('1',seqid.pair_id)

    def test_unrecognised_id_format(self):
        """Process an unrecognised sequence identifier
        """
        seqid_string = "@SEQID"
        seqid = SequenceIdentifier(seqid_string)
        # Check we get back what we put in
        self.assertEqual(str(seqid),seqid_string)
        # Check the format
        self.assertEqual(None,seqid.format)

class TestNReads(unittest.TestCase):
    """Tests of the nreads function
    """

    def test_nreads(self):
        """Check that nreads returns correct read count
        """
        fp = cStringIO.StringIO(fastq_data)
        self.assertEqual(nreads(fp=fp),5)

def run_tests():
    """Run the tests
    """
    logging.getLogger().setLevel(logging.CRITICAL)
    unittest.main()

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Run the tests
    run_tests()
