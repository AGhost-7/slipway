module DevDock

  class Options

    def initialize(argv)
      @volumes = []
      @environment = []
      @subcommand = nil
      @error = nil
      @argv = argv
    end

    def parse
      parse_subcommand @argv[0]
      if not @error
        if @subcommand == "start"
          parse_options @argv.slice(1, @argv.length)
        end
        if not @error
          @image_name = @argv.last
        end
      end
    end

    def parse_subcommand(arg)
      if arg == 'start' or arg == 's'
        @subcommand = 'start'
      elsif arg == 'purge' or arg == 'p'
        @subcommand = 'purge'
      else
        @error = "Invalid subcommand #{arg}"
      end
    end

    def parse_options(argv)
      i = 0
      while argv[i + 1]
        arg = argv[i]
        if arg == '--volume' or arg == '-v'
          @volumes.push argv[i + 1]
          i += 1
        elsif arg == '--env' or arg == '-e'
          if not argv[i + 2] or not argv[i + 1]
            @error = "Invalid use of option #{arg}"
            break
          else
            @environment.push argv[i + 1]
            i += 1
          end
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

    def image_name
      @image_name
    end

    def environment
      @environment
    end

    def inspect
      "Subcommand: #{@subcommand}, Image: #{@image_name}, Volumes: #{volumes}, Environment: "
    end

  end
end
