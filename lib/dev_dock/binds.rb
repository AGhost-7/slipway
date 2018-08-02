require 'fileutils'

module DevDock

  # binds are a type of mount which just map what is on the host into
  # the container
  class DevBind

    attr_reader :source, :target, :permissions

    def initialize(internal_volumes, source, target, permissions)
      @internal_volumes = internal_volumes
      @source = source
      @target = target
      @permissions = permissions
    end

    def exist?
      File.exist?(@source)
    end

    def create
      if not exist?
        if not File.directory?(@source)
          FileUtils.mkdir_p(File.dirname(@source))
          FileUtils.touch(@source)
        else
          FileUtils.mkdir_p(@source)
        end
      end
    end

    def host_path
      if @internal_volumes
        internal, host = parent_volume
        # just need to take out the part of the path which is internal, and
        # replace it with the host volume.
        relative = @source.slice(internal.length, @source.length)
        if relative.length == 0
          host
        else
          File.join(host, relative)
        end
      else
        @source
      end
    end

    def parent_volume
      @internal_volumes.find { |internal, host| @source.index(internal) == 0 }
    end

    def to_argument
      [host_path, @target, @permissions].compact.join(':')
    end

  end

  class DevBinds

    def initialize(list)
      @internal_volumes = nil
      @container = nil
      @list = list
    end

    def internal_volumes
      if container? and @internal_volumes.nil?
        container_id = File.read('/proc/1/cgroup')
          .lines
          .find { |cgroup| cgroup.include?('docker') }
          .split('/')
          .last
          .strip

        container = Docker::Container.get(container_id)
        @internal_volumes = container.json['Volumes']
      end
      @internal_volumes
    end

    def list
      @list.map do |item|
        source, target, permissions = item.split(':')
        DevBind.new(internal_volumes, source, target, permissions)
      end
    end

    def push(item)
      @list.push(item)
    end

    # check if we're currently running inside of a container
    def container?
      if @container.nil?
        if File.exist?('/proc/1/cgroup')
          @container = File.read('/proc/1/cgroup').include?('docker')
        else
          @container = false
        end
      end
      @container
    end

    def create
      list.each do |bind|
        bind.create
      end
    end

  end
end
