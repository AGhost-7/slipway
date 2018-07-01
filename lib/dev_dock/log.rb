module DevDock
  module Log
    def self.info(*stuff)
      puts *stuff
    end

    def self.debug(*stuff)
      if ENV['DEV_DOCK_DEBUG'] == '1'
        puts *stuff
      end
    end
  end
end
