#!/usr/bin/env ruby

require 'json'
require 'net/http'

VERSION = '2.0.0'

def greet(name)
  puts "Hello, #{name}!"
end

class Application
  attr_reader :config
  
  def initialize
    @config = {}
  end
end

if __FILE__ == $0
  app = Application.new
  greet("World")
end