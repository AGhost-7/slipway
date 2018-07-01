module DevDock
  module Util
    def self.snake_case(characters)
      characters.downcase.gsub(/\W/, '_')
    end
  end
end

