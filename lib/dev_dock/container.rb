require 'docker'
require 'dev_dock/util'
require 'dev_dock/image'
require 'dev_dock/volumes'

module DevDock

	class DevContainer

		def initialize(image_name)
			@image = DevDock::DevImage.new(image_name)
			@volumes = DevDock::DevVolumes.new(@image)
			@name = DevDock::Util::snake_case("dev_dock_#{image_name}")
		end

		def image
			@image
		end

		def volumes
			@volumes
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

    def enable_x11(arguments)
      if File.exist? '/tmp/.X11-unix'
        Log::debug('X11 socket file found')
        arguments.push '-v'
        arguments.push '/tmp/.X11-unix:/tmp/.X11-unix:ro'
        arguments.push '-e'
        arguments.push 'DISPLAY'
      else
        Log::debug('Did not find X11 socket file')
      end
    end

		def run
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
				'-v', '/run/docker.sock:/var/run/docker.sock'
			]

			['workspaces', '.gitconfig', '.ssh'].each do |directory|
				arguments.push '-v', "#{ENV['HOME']}/#{directory}:/home/#{@image.user}/#{directory}"
			end

			if RUBY_PLATFORM.start_with?("x86_64-linux")
				enable_x11(arguments)
				arguments.push '-v', '/etc/localhost:/etc/localhost:ro'
			end

			@volumes.list.each do |volume|
				arguments.push '--mount', "source=#{volume.name},target=#{volume.path}"
			end

			arguments.push @image.name

			arguments.push 'tmux'
			arguments.push 'new'

			exec *arguments
		end
	end
end
