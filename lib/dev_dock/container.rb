require 'docker'
require 'dev_dock/binds'
require 'dev_dock/util'
require 'dev_dock/image'
require 'dev_dock/volumes'

module DevDock

  class DevContainer

    attr_reader :image, :volumes, :binds

    def initialize(options)
      @options = options
      @image = DevDock::DevImage.new(options.image_name)
      @volumes = DevDock::DevVolumes.new(@image)
      @binds = DevDock::DevBinds.new([
        '/var/run/docker.sock:/var/run/docker.sock'
      ])
      @name = DevDock::Util::snake_case("dev_dock_#{options.image_name}")

      init_binds
    end

    def init_binds

      ['workspaces', '.gitconfig', '.ssh'].each do |directory|
        source = File.join(ENV['HOME'], directory)
        target = File.join("/home", @image.user, directory)
        @binds.push("#{source}:#{target}")
      end

      if x11?
        @binds.push('/tmp/.X11-unix:/tmp/.X11-unix:ro')
      end

      if linux?
        @binds.push( '/etc/localtime:/etc/localtime:ro')
      end
    end

    def docker_group
      docker_line = File
        .read('/etc/group')
        .lines
        .find { |line| line.start_with?('docker') }
      group = docker_line and docker_line.split(':')[1]
      if docker_line.nil?
        group = docker_line
      else
        group = docker_line.split(':')[2]
      end
      Log::debug("Docker gid is #{group}")
      group
    end

    def exist?
      Docker::Container.get(@name)
      true
    rescue Docker::Error::NotFoundError
      false
    end

    # kill container
    def kill
      Docker::Container.get(@name).kill		
    end

    def x11?
      File.exists?('/tmp/.X11-unix')
    end

    def linux?
      RUBY_PLATFORM.start_with?("x86_64-linux")
    end

    def enable_x11(arguments)
      if x11?
        Log::debug('X11 socket file found')
        arguments.push '-e'
        arguments.push 'DISPLAY'
      else
        Log::debug('Did not find X11 socket file')
      end
    end

    def run_arguments
      arguments = [
        'docker',
        'run',
        '--privileged',
        '--name', @name,
        '--group-add', docker_group,
        '--net=host',
        '--rm',
        '-ti',
        '--detach-keys',
        'ctrl-q,ctrl-q',
        '-e', 'GH_USER',
        '-e', 'GH_PASS',
        '-e', "DEV_DOCK_HOST_HOME=#{@options.host_home}"
      ]

      if linux?
        enable_x11(arguments)
      end

      @volumes.list.each do |volume|
        arguments.push '--mount', "source=#{volume.name},target=#{volume.path}"
      end

      @options.volumes.each do |volume|
        arguments.push '-v', volume
      end

      @binds.list.each do |bind|
        arguments.push '-v', bind.to_argument
      end

      @options.environment.each do |environment|
        arguments.push '-e', environment
      end

      arguments.push @image.name

      arguments.push *@options.run_command

      arguments
    end

    def run
      exec *run_arguments
    end
  end
end
