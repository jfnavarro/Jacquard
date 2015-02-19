from StringIO import StringIO
from argparse import Namespace
import os
from re import findall, MULTILINE
import sys
import unittest

from testfixtures import TempDirectory

import jacquard.logger as logger
import jacquard.utils as utils
import jacquard.variant_callers.strelka as strelka
import jacquard.variant_callers.varscan as varscan
import test.test_case as test_case
import test.vcf_test as vcf_test
import jacquard.translate as translate

class TranslateTestCase(test_case.JacquardBaseTestCase):
    def setUp(self):
        super(TranslateTestCase, self).setUp()

    def test_predict_output(self):
        with TempDirectory() as input_dir:
            input_dir.write("A.vcf", "##source=strelka\n#colHeader")
            input_dir.write("B.vcf", "##source=strelka\n#colHeader")
            args = Namespace(input=input_dir.path)

            desired_output_files = translate._predict_output(args)
            expected_desired_output_files = set(["A.translatedTags.vcf",
                                                 "B.translatedTags.vcf"])

            self.assertEquals(expected_desired_output_files, desired_output_files)

#     def test_check_records(self):
#         

class TranslateFunctionalTestCase(test_case.JacquardBaseTestCase):
    def Xtest_translate(self):
        with TempDirectory() as output_file:
            test_dir = os.path.dirname(os.path.realpath(__file__))
            module_testdir = os.path.join(test_dir, "functional_tests", "01_translate")
            input_file = os.path.join(module_testdir, "input")

            command = ["translate", input_file, output_file.path, "--force"]
            expected_dir = os.path.join(module_testdir, "benchmark")

            self.assertCommand(command, expected_dir)