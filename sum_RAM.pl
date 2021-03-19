#!/usr/bin/env perl

use warnings;
use strict;

my @sums = (0, 0, 0, 0, 0, 0);
while (<>) {
    print $_;
    next if $_ =~ /^#/ or $_ =~ /^---/;
    chomp;
    my $line = $_;
    s/^\s+//;
    my @data = split /\s*\|\s*/;
    #print join(",", @data), "\n";
    for my $i (0..6) {
	$sums[$i] += $data[$i];
    }
}

my $format = "%11.3f";
for my $i (0..6) {
    $sums[$i] = sprintf $format, $sums[$i];
}
$sums[0] = "      ";
print join(" | ", @sums), " |\n";
