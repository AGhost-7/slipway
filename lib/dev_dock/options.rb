module DevDock

  class Options

    def initialize(argv)
      @volumes = []
      @error = nil
    end

    def parse
      parse_subcommand @argv[0]
      if not @error
        parse_options @argv.slice(1, @argv.length)
      end
    end

    def parse_subcommand(argv)
      subcommand = argv[0]
      if subcommand == "start" or subcommand == "s"
        @sudcommand = "start"
      elsif subcommand == "purge" or subcommand == "p"
        @subcommand = "purge"
      else
        @error = "Invalid subcommand #{subcommand}"
      end
    end

    def parse_options(argv)
      i = 1
      while argv[i]
        arg = argv[i]
        if arg == '--volume' or arg == '-v'
          @volumes.push arg[i + 1]
          i += 1
        else
          @error = "Invalid option: #{arg}"
          break
        end
        i += 1
      end
    end

    def subcommand
      @subcommand
    end

    def error
      @error
    end

    def volumes
      @volumes
    end
  end
end
