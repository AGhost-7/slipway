require 'docker'
require 'dev_dock/util'
require 'dev_dock/log'

# Automatically generated volumes based on what the image has listed in its
# dockerfile

module DevDock

	# Volume which is needed for the development environment
	class DevVolume
		def initialize(image_name, path)
			@path = path
			@name = DevDock::Util::snake_case("dev_dock_#{image_name}#{path}")
		end

		def name
			@name
		end

		def path
			@path
		end

		# returns true if the volume exists
		def exist?
			volumes = Docker::Util.parse_json(Docker.connection.get('/volumes'))["Volumes"]
			Log::debug("Volumes in docker: #{volumes}")
			volumes.any? { |volume| volume['Name'] == @name }
		end

		# creates the volume if it does not exist
		def create
			Log::debug("Checking volume #{@name} for path #{@path}")
			if !exist?
				Log::info("Creating volume #{@name}")
				Docker::Volume.create(@name)
			end
		end

		# removes the volume if it exists
		def remove
			Log::debug("Checking volume #{@name} for path #{@path}")
			if exist?
				Log::info("Removing volume #{@name})")
				Docker::Volume.get(@name).remove
			end
		end
	end

	# Collection representing volumes needed for then development environment
	class DevVolumes
		def initialize(image)
			@image = image
		end

		def name
			@name
		end

		# returns a list of volumes with their names and paths
		def list
			if @image.container_config['Volumes'].nil?
				[]
			else
				@image.container_config['Volumes'].keys.map do |path|
						DevVolume.new(@image.name, path)
				end
			end
		end

		# returns the volume for the given volume path
		def get(path)
			if ! @image.container_config['Volumes'].keys.includes? path
				nil
			else
				DevVolume.new(@image.name, path)
			end
		end

		# creates all desired volumes based on the configuration in the image
		def create
			Log::debug 'DevVolumes::create'
			list.each do |volume|
				volume.create
			end
		end

		# purges all related volumes
		def remove
			puts 'DevVolumes::remove'
			list.each do |volume|
				volume.remove
			end
		end
	end

end
