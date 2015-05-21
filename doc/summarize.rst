Summarize
---------
The summarize command uses the Jacquard-specific tags to aggregate caller
information from the file, providing a summary-level view. The inclusion of
summary fields, such as averages, helps you to easily determine which are the
true variants.

The summarized format tags contain the prefix 'JQ_SUMMARY'.

.. figure:: images/summarize.jpg

   **Summarizing Format Tags :** *The Jacquard-translated format tags from
   each caller are aggregated and processed together to create consensus format
   tags.* 

|

Usage
^^^^^
``usage: jacquard summarize <input_file> <output_file>``


*positional arguments:*

=====================   =======================================================
input                   Jacquard-merged VCF file (or any VCF with Jacquard
                        tags; e.g. JQ_SOM_MT)
output                  VCF file
=====================   =======================================================