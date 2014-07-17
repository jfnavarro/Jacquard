#!/usr/bin/python2.7
from collections import OrderedDict, defaultdict
import glob
import os
from os import listdir
from os.path import isfile, join
import shutil


class Varscan():
    def __init__(self):
        self.name = "VarScan"
    
    def validate_input_file(self, input_file):
        valid = 0
        for line in input_file:
            if line.startswith("##source=VarScan2"):
                valid = 1
            elif line.startswith("##"):
                continue
            else:
                break
        return (self.name, valid)
        
class Mutect():
    def __init__(self):
        self.name = "MuTect"
    
    def validate_input_file(self, input_file):
        valid = 0
        for line in input_file:
            if line.startswith("##MuTect"):
                valid = 1
            elif line.startswith("##"):
                continue
            else:
                break
        return (self.name, valid)
     
class Unknown():
    def __init__(self):
        self.name = "Unknown"
        
    def validate_input_file(self, input_file):
        valid = 1
        return (self.name, valid)
    
    
class Varscan_AlleleFreqTag():
    def __init__(self):
        self.metaheader = '##FORMAT=<ID=JQ_AF_VS,Number=1,Type=Float, Description="Jacquard allele frequency for VarScan: Decimal allele frequency rounded to 2 digits (based on FREQ).">\n'

    def format(self, info_string, format_param_string, format_value_string, count):
        format_param_array = format_param_string.split(":")
        format_value_array = format_value_string.split(":")
        format_dict = dict(zip(format_param_array, format_value_array))
        
        if "FREQ" in format_dict.keys():
            format_value_string += ":" + self.roundTwoDigits(format_dict["FREQ"])
            format_param_string += ":JQ_AF_VS"
            
        return format_param_string, format_value_string

    def roundTwoDigits(self, value): 
        value = str(float(value.strip("%"))/100)
        if len(value.split(".")[1]) <= 2:
            return value
        else:
            return str(round(100 * float(value))/100) 
        
class Varscan_DepthTag():
    def __init__(self):
        self.metaheader = '##FORMAT=<ID=JQ_DP_VS,Number=1,Type=Float, Description="Jacquard depth for VarScan (based on DP).">\n'

    def format(self, info_string, format_param_string, format_value_string, count):
        format_param_array = format_param_string.split(":")
        format_value_array = format_value_string.split(":")
        format_dict = dict(zip(format_param_array, format_value_array))
        
        if "DP" in format_dict.keys():
            format_value_string += ":" + format_dict["DP"]
            format_param_string += ":JQ_DP_VS"
            
        return format_param_string, format_value_string
    
class Varscan_SomaticTag():
    def __init__(self):
        self.metaheader = '##FORMAT=<ID=JQ_SOM_VS,Number=1,Type=Integer,Description="Jacquard somatic status for VarScan: 0=non-somatic,1= somatic (based on SOMATIC info tag and if sample is TUMOR).">\n'
#  
    def format(self, info_string, format_param_string, format_value_string, count):
        info_array = info_string.split(";")

        if "SS=2" in info_array:
            format_value_string += ":" + self.somatic_status(count)
            format_param_string += ":JQ_SOM_VS"
        return format_param_string, format_value_string
#  
    def somatic_status(self, count):
        if count == 0: #it's NORMAL
            return "0"
        else: #it's TUMOR
            return "1"

class Mutect_AlleleFreqTag():
    def __init__(self):
        self.metaheader = '##FORMAT=<ID=JQ_AF_MT,Number=1,Type=Float, Description="Jacquard allele frequency for MuTect: Decimal allele frequency rounded to 2 digits (based on FA).">\n'

    def format(self, info, format_param_string, format_value_string, count):
        format_param_array = format_param_string.split(":")
        format_value_array = format_value_string.split(":")
        format_dict = dict(zip(format_param_array, format_value_array))
        
        if "FA" in format_dict.keys():
            format_value_string += ":" + self.roundTwoDigits(format_dict["FA"])
            format_param_string += ":JQ_AF_MT"
            
        return format_param_string, format_value_string

    def roundTwoDigits(self, value): 
        if len(value.split(".")[1]) <= 2:
            return value
        else:
            return str(round(100 * float(value))/100) 
        
class Mutect_DepthTag():
    def __init__(self):
        self.metaheader = '##FORMAT=<ID=JQ_DP_MT,Number=1,Type=Float, Description="Jacquard depth for MuTect (based on DP).">\n'

    def format(self, info, format_param_string, format_value_string, count):
        format_param_array = format_param_string.split(":")
        format_value_array = format_value_string.split(":")
        format_dict = dict(zip(format_param_array, format_value_array))
        
        if "DP" in format_dict.keys():
            format_value_string += ":" + format_dict["DP"]
            format_param_string += ":JQ_DP_MT"
            
        return format_param_string, format_value_string
    
class Mutect_SomaticTag():
    def __init__(self):
        self.metaheader = '##FORMAT=<ID=JQ_SOM_MT,Number=1,Type=Integer,Description="Jacquard somatic status for MuTect: 0=non-somatic,1= somatic (based on SS FORMAT tag).">\n'

    def format(self, info, format_param_string, format_value_string, count):
        format_param_array = format_param_string.split(":")
        format_value_array = format_value_string.split(":")
        format_dict = dict(zip(format_param_array, format_value_array))
        
        if "SS" in format_dict.keys():
            format_value_string += ":" + self.somatic_status(format_dict["SS"])
            format_param_string += ":JQ_SOM_MT"
            
        return format_param_string, format_value_string

    def somatic_status(self, ss_value):
        if ss_value == "2":
            return "1"
        else:
            return "0"

class LineProcessor():
    def __init__(self, tags):
        self.tags = tags
        
    def add_tags(self, input_line):
        no_newline_line = input_line.rstrip("\n")
        original_vcf_fields = no_newline_line.split("\t")
        new_vcf_fields = original_vcf_fields[:8]
        info = original_vcf_fields[7]
        format = original_vcf_fields[8]
        samples = original_vcf_fields[9:]

        count = 0
        for sample in samples:
            format_dict = OrderedDict()
            for tag in self.tags:
                param, value = tag.format(info, format, sample, count)
                param_list = param.split(":")
                value_list = value.split(":")
                for i in range(0, len(param_list)):
                    format_dict[param_list[i]] = value_list[i]

            if count < 1: ##only add format column once
                new_vcf_fields.append(":".join(format_dict.keys()))
            new_vcf_fields.append(":".join(format_dict.values()))
            count += 1

        return "\t".join(new_vcf_fields) + "\n"

class FileProcessor():
    
    def __init__(self, tags=[], execution_context_metadataheaders = []):
        self._tags = tags
        self._metaheader = self._metaheader_handler(execution_context_metadataheaders)
        
        for tag in self._tags:
            self._metaheader += tag.metaheader
        self._lineProcessor = LineProcessor(self._tags)
            
    def _metaheader_handler(self, metaheaders):
        new_headers = ["##{}\n".format(header) for header in metaheaders]
        return ''.join(new_headers)

    def process(self, reader, writer, caller):
        for line in reader:
            if line.startswith("##"):
                writer.write(line)
            elif line.startswith("#"):
                if caller == "VarScan":
                    if "NORMAL" in line and "TUMOR" in line:
                        writer.write(self._metaheader)
                        writer.write(line)
                    else:
                        print "Unexpected VarScan VCF structure - missing NORMAL\t and TUMOR\n headers."
                        exit(1)
                elif caller == "MuTect":
                    writer.write(self._metaheader)
                    writer.write(line)
            else:
                edited_line = self._lineProcessor.add_tags(line)
                writer.write(edited_line)


def add_subparser(subparser):
    parser_tagVarscan = subparser.add_parser("tag", help="Accepts a directory of VCf results and creates a new directory of VCFs, adding Jacquard-specific FORMAT tags for each VCF record.")
    parser_tagVarscan.add_argument("input_dir")
    parser_tagVarscan.add_argument("output_dir")

def validate_directories(input_dir, output_dir):    
    if not os.path.isdir(input_dir):
        print "Error. Specified input directory {0} does not exist".format(input_dir)
        exit(1)
    try:
        listdir(input_dir)
    except:
        print "Error: Specified input directory [{0}] cannot be read. Check permissions and try again.".format(input_dir)
        exit(1)
        
    if not os.path.isdir(output_dir):
        try:
            os.makedirs(output_dir)
        except:
            print "Error: Output directory could not be created. Check parameters and try again"
            exit(1)

def determine_file_types(input_dir, in_files, callers):
    file_types = defaultdict(list)                                       
    for file in in_files:
        for caller in callers:
            in_file = open(os.path.join(input_dir, file), "r")
            caller_name, valid = caller.validate_input_file(in_file)
            if valid == 1:
                file_types[caller_name].append(file)
                print "{0}:##jacquard.tag.handler={1}".format(os.path.basename(file), caller_name)
                break
    return file_types
    
def tag_files(input_dir, output_dir, callers, input_metaheaders=[]):
    processors = {"VarScan" : FileProcessor(tags=[Varscan_AlleleFreqTag(), Varscan_DepthTag(), Varscan_SomaticTag()], execution_context_metadataheaders=input_metaheaders), "MuTect": FileProcessor(tags=[Mutect_AlleleFreqTag(), Mutect_DepthTag(), Mutect_SomaticTag()], execution_context_metadataheaders=input_metaheaders)}
    
    in_files = sorted(glob.glob(os.path.join(input_dir,"*.vcf")))
    if len(in_files) < 1:
        print "Error: Specified input directory [{0}] contains no VCF files. Check parameters and try again."
        exit(1)
        
    print "\n".join(input_metaheaders)
    print "Processing [{0}] VCF file(s) from [{1}]".format(len(in_files), input_dir)
    
    file_types = determine_file_types(input_dir, in_files, callers)
    for key, vals in file_types.items():
        print "Recognized [{0}] {1} files".format(len(vals), key)
    if "Unknown" in file_types.keys():
        print "Error: unable to determine which caller was used on [{0}]. Check input files and try again.".format(file_types["Unknown"])
        exit(1)
    
    for file in in_files:
        fname, extension = os.path.splitext(os.path.basename(file))
        new_file = fname + "_jacquard" + extension
        
        in_file = open(os.path.join(input_dir, file), "r")
        out_file = open(os.path.join(output_dir, new_file), "w")
        
        for key, vals in file_types.items():
            if file in vals:
                processors[key].process(in_file, out_file, key)
        
        in_file.close()
        out_file.close()

    out_files = sorted(glob.glob(os.path.join(output_dir,"*.vcf")))
    
    print "Wrote [{0}] VCF file(s) to [{1}]".format(len(out_files), output_dir)

def execute(args, execution_context): 
    input_dir = os.path.abspath(args.input_dir)
    output_dir = os.path.abspath(args.output_dir)
    
    validate_directories(input_dir, output_dir)
    
    callers = [Mutect(), Varscan(), Unknown()]
    tag_files(input_dir, output_dir, callers, execution_context)
    