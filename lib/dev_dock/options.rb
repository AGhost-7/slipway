require 'optparse'

module DevDock

  # Handles parsing options with the following syntax:
  # dev_dock subcommand [options..] image [command..]

  class Options

    def initialize(argv)
      @volumes = []
      @environment = []
      @subcommand = nil
      @error = nil
      @image_name = nil
      @argv = argv
      @run_command = ['tmux', 'new']
    end

    def parse
      parse_subcommand

      if not @error
        if @subcommand == "start"
          parse_start
        else
          parse_end
        end
      end

    end

    def parse_end
      if @argv.length != 2
        @error = 'Invalid number of arguments'
      else
        @image_name = @argv[1]
      end
    end

    def parse_start
      parser = OptionParser.new 'Usage: dev_dock start [options..] image [command..]'

      parser.on('-e', '--env ENVIRONMENT') do |env|
        self.environment.push(env)
      end
      parser.on('-v', '--volume VOLUME') do |volume|
        self.volumes.push(volume)
      end
      argv = @argv.slice(1, @argv.length - 1)
      begin
        parser.parse!(argv)
      rescue OptionParser::ParseError => err
        @error = err.reason
      end

      if not @error
        if argv.length == 0
          @error = 'Missing argument: image'
        else
          @image_name = argv.shift()
          if argv.length > 0
            @run_command = argv
          end
        end
      end
    end

    def parse_subcommand
      arg = @argv[0]
      if arg == 'start' or arg == 's'
        @subcommand = 'start'
      elsif arg == 'purge' or arg == 'p'
        @subcommand = 'purge'
      else
        @error = "Invalid subcommand #{arg}"
      end
    end

    attr_reader :run_command, :subcommand, :error, :volumes, :image_name, :environment

    def inspect
      "Subcommand: #{@subcommand}, Image: #{@image_name}, Volumes: #{@volumes}, Environment: #{@environment}, Run Command: #{@run_command}"
    end

  end
end
