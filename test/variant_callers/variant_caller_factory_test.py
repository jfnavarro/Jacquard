#pylint:disable=line-too-long,invalid-name,global-statement, too-many-public-methods
import test.test_case as test_case
import jacquard.variant_callers.variant_caller_factory as variant_caller_factory
from jacquard.utils import JQException
import test.vcf_test as vcf_test

original_callers = None

class VariantCallerFactoryTestCase(test_case.JacquardBaseTestCase):
    def test_defined_caller(self):
        self.assertEquals(3, len(variant_caller_factory._CALLERS))
        caller_names = [caller.name for caller in variant_caller_factory._CALLERS]
        self.assertIn('VarScan', caller_names)
        self.assertIn('MuTect', caller_names)
        self.assertIn('Strelka', caller_names)

    def test_caller_notFoundRaisesException(self):
        self.assertRaises(JQException,
                          variant_caller_factory.get_caller,
                          ["##metaheaders"],
                          "#header",
                          "vcfName")

class VariantCallerFactoryClaimTestCase(test_case.JacquardBaseTestCase):
    def setUp(self):
        super(VariantCallerFactoryClaimTestCase, self).setUp()
        global original_callers
        original_callers = list(variant_caller_factory._CALLERS)

    def tearDown(self):
        variant_caller_factory._CALLERS = original_callers
        super(VariantCallerFactoryClaimTestCase, self).tearDown()

    def test_claim(self):
        fileA = vcf_test.MockFileReader("fileA.vcf")
        fileB = vcf_test.MockFileReader("fileB.vcf")
        fileC = vcf_test.MockFileReader("fileC.vcf")
        file_readers = [fileA,
                        fileB,
                        fileC]
        variant_caller_factory._CALLERS = [vcf_test.MockCaller("foo", claimable=[fileC]),
                                           vcf_test.MockCaller("bar", claimable=[fileB]),
                                           vcf_test.MockCaller("baz", claimable=[fileA])]
        expected = [fileC, fileB, fileA]
        _, actual = variant_caller_factory.claim(file_readers)
        self.assertEquals(expected, actual)

    def test_claim_unclaimedFilesRemain(self):
        fileA = vcf_test.MockFileReader("fileA.vcf")
        fileB = vcf_test.MockFileReader("fileB.vcf")
        unclaimable_file = vcf_test.MockFileReader("fileC.txt")
        file_readers = [fileA,
                        fileB,
                        unclaimable_file]
        variant_caller_factory._CALLERS = [vcf_test.MockCaller("foo", claimable=[fileB]),
                                           vcf_test.MockCaller("bar", claimable=[fileA])]
        expected_unclaimed = [unclaimable_file]
        actual_unclaimed, _ = variant_caller_factory.claim(file_readers)

        self.assertEquals(expected_unclaimed, actual_unclaimed)
