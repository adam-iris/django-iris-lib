flour = require 'flour'
fs = require 'fs'
path = require 'path'
minimatch = require 'minimatch'

flour.minifiers.js = null
flour.compilers.less.compress = false

basePath = 'www/static'
baseLessPath = "#{basePath}/less"
baseCssPath = "#{basePath}/css"

task 'build:less', ->
  compile "#{baseLessPath}/fdsn.less", "#{baseCssPath}/fdsn.css"

task 'watch:less', ->
  watch "#{baseLessPath}/*.less", -> invoke 'build:less'

task 'build', ->
  invoke 'build:less'

task 'watch', ->
  invoke 'build'
  invoke 'watch:less'

task 'lint', 'Check javascript syntax', ->
  lint 'js/feature.js'