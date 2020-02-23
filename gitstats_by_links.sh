#!/bin/bash

set -e # abort upon error

declare -a paths=(
                  #"https://github.com/homalg-project/CAP_project"
                  #"https://github.com/homalg-project/homalg_project"
                  "https://github.com/homalg-project/QuotientCategories"
                  "https://github.com/homalg-project/StableCategories"
                  "https://github.com/homalg-project/FrobeniusCategories"
                  "https://github.com/homalg-project/ComplexesForCAP"
                  "https://github.com/homalg-project/Bicomplexes"
                  "https://github.com/homalg-project/HomotopyCategories"
                  "https://github.com/homalg-project/DerivedCategories"
                  "https://github.com/homalg-project/ModelCategories"
                  "https://github.com/homalg-project/BBGG"
                  "https://github.com/homalg-project/NConvex"
                  "https://github.com/homalg-project/CddInterface"
                  )

for rep_path in "${paths[@]}"
do
  echo "creating gitstats of $rep_path"
  git clone ${rep_path}
  rep_name=$(echo $rep_path| cut -d'/' -f 5)
  cd html
  rm -Rf ${rep_name}
  mkdir ${rep_name}
  cd ..
  ./gitstats ${rep_name} $(pwd)/html/${rep_name}
  rm -rf ${rep_name}
done
