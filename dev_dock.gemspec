
lib = File.expand_path("../lib", __FILE__)
$LOAD_PATH.unshift(lib) unless $LOAD_PATH.include?(lib)
require "dev_dock/version"

Gem::Specification.new do |spec|
  spec.name          = "dev_dock"
  spec.version       = DevDock::VERSION
  spec.authors       = ["AGhost-7"]
  spec.email         = ["jonathan.boudreau.92@gmail.com"]

	spec.summary       = "Manage your docker development environments."
	spec.description   = "Manage your development environment (including editor) using docker."
	spec.homepage      = "https://github.com/AGhost-7/dev-dock"
  spec.license       = "MIT"

  # Specify which files should be added to the gem when it is released.
  # The `git ls-files -z` loads the files in the RubyGem that have been added into git.
  spec.files         = Dir.chdir(File.expand_path('..', __FILE__)) do
    `git ls-files -z`.split("\x0").reject { |f| f.match(%r{^(test|spec|features)/}) }
  end
  spec.executables   = ['dev_dock']
  spec.require_paths = ["lib"]

  spec.add_development_dependency "bundler", "~> 1.16"
  spec.add_development_dependency "rake", "~> 10.0"
  spec.add_development_dependency "rspec", "~> 3.0"

	spec.add_dependency "docker-api", "~> 1.34"
end
