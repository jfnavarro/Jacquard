from collections import OrderedDict
import os 
import unittest

import jacquard.utils as utils
from jacquard.expand2 import _parse_meta_headers, \
    _append_format_tags_to_samples, _get_headers, _write_vcf_records, \
    _disambiguate_column_names, _filter_and_sort

TEST_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

class MockVcfReader(object):
    def __init__(self, input_filepath="vcfName", metaheaders=["##metaheaders"], column_header="#header", content = ["foo"]):
        self.input_filepath = input_filepath
        self.metaheaders = metaheaders
        self.column_header = column_header
        self.opened = False
        self.closed = False
        self.content = content

    def open(self):
        self.opened = True

    def vcf_records(self):
        for content in self.content:
            yield MockVcfRecord(content)

    def close(self):
        self.closed = True

class MockVcfRecord(object):
    def __init__(self, content):
        self.chrom, self.pos, self.id, self.ref, self.alt, self.qual, \
            self.filter, self.info, self.format = content[0:9]
        self.samples = content[9:]

        tags = self.format.split(":")
        self.sample_dict = {}
        for i, sample in enumerate(self.samples):
            values = sample.split(":")
            self.sample_dict[i] = OrderedDict(zip(tags, values))

    def get_info_dict(self):
        info_dict = {}

        for key_value in self.info.split(";"):
            if "=" in key_value:
                key,value = key_value.split("=")
                info_dict[key] = value
            else:
                info_dict[key_value] = key_value

        return info_dict

class MockFileWriter(object):
    def __init__(self):
        self.written = []

    def write(self, text):
        self.written.append(text)

class ExpandTestCase(unittest.TestCase):
    def test_parse_meta_headers(self):
        meta_headers = ['##ALT=<ID=DEL,Description="Deletion">',
                        '##INFO=<ID=AC,Number=.,Description="foo">]',
                        '##INFO=<ID=AA,Number=1,Description="Ancestral Allele"',
                        '##FORMAT=<ID=SP,Type=Integer,Description="bar">',
                        '##RUNTIME_ARG=allele freq. cutoff: 5']
        (info_fields, format_tags) = _parse_meta_headers(meta_headers)

        self.assertEquals(["AA", "AC"], info_fields)
        self.assertEquals(["SP"], format_tags)

    def test_parse_meta_headers_missing(self):
        meta_headers = ['##ALT=<ID=DEL,Description="Deletion">',
                        '##INFO=<ID=AC,Number=.,Description="foo">]',
                        '##INFO=<ID=AA,Number=1,Description="Ancestral Allele"',
                        '##RUNTIME_ARG=allele freq. cutoff: 5']

        self.assertRaisesRegexp(utils.JQException,
                                    "Unable to parse meta_headers for INFO " +
                                    "and/or FORMAT fields. Review input and " +
                                    "try again.",
                                    _parse_meta_headers,
                                    meta_headers)

    def test_disambiguate_column_names(self):
        column_header = ["CHROM", "POS", "ID", "REF"]
        info_header = ["HOM", "AA", "SOM"]

        actual = _disambiguate_column_names(column_header, info_header)
        expected = ["HOM", "AA", "SOM"]

        self.assertEquals(expected, actual)

        column_header = ["CHROM", "POS", "ID", "REF"]
        info_header = ["HOM", "AA", "ID", "SOM"]
        actual = _disambiguate_column_names(column_header, info_header)
        expected = ["INFO_HOM", "INFO_AA", "INFO_ID", "INFO_SOM"]

        self.assertEquals(expected, actual)

    def test_append_format_tags_to_samples(self):
        format_tags = ["bar", "foo"]
        samples = ["sampleA", "sampleB"]
        actual = _append_format_tags_to_samples(format_tags, samples)

        expected = ["bar|sampleA", "foo|sampleA", "bar|sampleB", "foo|sampleB"]

        self.assertEquals(expected, actual)

    def test_get_headers(self):
        meta_headers = ['##ALT=<ID=DEL,Description="Deletion">',
                        '##INFO=<ID=AC,Number=.,Description="foo">]',
                        '##INFO=<ID=AA,Number=1,Description="Ancestral Allele"',
                        '##FORMAT=<ID=SP,Number=1,Description="bar">',
                        '##RUNTIME_ARG=allele freq. cutoff: 5']

        col_header = "CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tsampleA\tsampleB"
        mock_reader = MockVcfReader(metaheaders=meta_headers,
                                    column_header= col_header)
        actual = _get_headers(mock_reader)

        expected = (["CHROM","POS","ID","REF","ALT","QUAL","FILTER"],
                    ["AA","AC"],
                    ["SP|sampleA","SP|sampleB"])

        self.assertEquals(expected, actual)

    def test_write_vcf_records(self):
        column_header = "CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tsampleA"

        mock_vcf_reader = MockVcfReader(content=[["CHROM","POS","ID","REF",
                                                  "ALT","QUAL","FILTER",
                                                  "tag1=val1;tag3=val3;tag4",
                                                  "FOO:BAR","42:1"]],
                                        column_header=column_header)

        mock_file_writer = MockFileWriter()

        info_header = ["tag1", "tag2", "tag3", "tag4"]
        format_sample_header = ["BAR|sampleA", "FOO|sampleA"]

        split_column_header = column_header.split("\t")[0:7]
        
        header_dict = {"column_header": split_column_header, "info_header":
                       info_header, "format_header": format_sample_header}
        _write_vcf_records(mock_vcf_reader, mock_file_writer, header_dict)

        actual = mock_file_writer.written
        expected = ["CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tval1\t\tval3\ttag4\t1\t42\n"]

        self.assertEquals(expected, actual)

    def xtest_filter_and_sort(self):
        header = {"column_header": ["CHROM", "POS", "ID"], "info_header":
                  ["infoA", "infoB", "infoC"], "format_header":
                   ["tagA|sample1", "tagB|sample1", "tagC|sample1"]}
        columns_to_expand = ["^CHROM$", "^info*", "^tagA\|*"]
        actual_header_dict = _filter_and_sort(header, columns_to_expand)
        expected_header = {'column_header': ["CHROM"], 'format_header': ['tagA|sample1'], 'info_header': ["infoA", "infoB", "infoC"]}
        
        self.assertEquals(expected_header, actual_header_dict)
        
        columns_to_expand = ["^CHROM$", "^tagA\|*", "ID", "POS"]
        actual_header = _filter_and_sort(header, columns_to_expand)
        
        expected_header = {'column_header': ["CHROM", "ID", "POS"], 'format_header': ['tagA|sample1'], 'info_header': []}
        self.assertEquals(expected_header, actual_header)
